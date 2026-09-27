# Curso music21 no piano roll — Fase 1 (infraestrutura + módulos 01-05) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared plumbing (`reaper_bridge` extensions + `curso_music21/_shared`) and the first 5 lesson modules (Notas e Alturas, Ritmo, Escalas e Tonalidades, Intervalos, Acordes e Tríades) of the music21-in-REAPER-piano-roll course, each a runnable `licao.py` + README.

**Architecture:** Each lesson script is `python curso_music21/modulos/NN_xxx/licao.py`, run with REAPER already open. It calls a pure `build_*()` function (music21 only, no I/O — unit-testable) and a `main()` that connects to REAPER (`lesson_track()`, new shared helper) and writes the result to a dedicated, auto-cleared MIDI track using `reaper_bridge`. Three small, reusable additions to `reaper_bridge` (not course-specific) make this possible: `get_or_create_track` / `clear_track_items` (`project.py`) and `write_events_to_track` / `write_score_to_tracks` (`midi.py`, variable-duration and multi-part writing — `write_notes_to_track` only supports fixed-length, single-part sequences today).

**Tech Stack:** Python 3.11, music21 10.5.0, reapy (REAPER live connection), pytest, existing `tests/fakes.py` fake-REAPER objects.

**Spec:** `docs/superpowers/specs/2026-09-27-curso-music21-design.md`

## Global Constraints

- REAPER must be open with reapy configured (`reapy.configure_reaper()`, run from the main repo venv, never a worktree) for any `licao.py` to work end-to-end — see `[[feedback_reapy_configure_from_main_repo]]`.
- Every function that talks to REAPER via reapy must raise `ReaperBridgeError` on failure, never let a raw reapy/REAPER exception propagate, and have a test that pins that behavior.
- Lessons reuse existing `reaper_bridge` functions (`generate_scale`, `generate_chord`, `write_notes_to_track`, etc.) instead of duplicating music21/reapy logic.
- Every `licao.py` separates a pure `build_*()` function (music21 only, no REAPER — unit-testable without REAPER open) from `main()` (the only part doing I/O).
- music21 User's Guide and Open Music Theory (CC BY-NC-SA, https://viva.pressbooks.pub/openmusictheory/) are cited/linked in READMEs, never copied verbatim.
- `curso_music21/modulos/NN_xxx` directory names start with digits, so they are **not** valid dotted-import targets for `from x.y import z` statements — tests import them with `importlib.import_module("curso_music21.modulos.NN_xxx.licao")` (verified working: Python's import machinery accepts non-identifier path segments via `importlib.import_module`, only the `import` statement's parser requires identifiers).

## Review Focus

- REAPER unavailable when a lesson runs must produce a friendly `ReaperBridgeError`, not a hang or raw traceback — pinned in Task 5 (`lesson_track` propagates `ReaperBridgeError`).
- Running the same lesson twice must not duplicate notes on its track (idempotency) — pinned in Task 5 (`lesson_track` clears existing items before writing).
- An ambiguous track name (two existing tracks already share it) must raise, not silently create a third — pinned in Task 2 (`get_or_create_track`).
- An empty event list must not create an empty MIDI item — pinned in Task 3 (`write_events_to_track`).
- A score with no notes in any part must not silently create empty tracks — pinned in Task 4 (`write_score_to_tracks`).

---

## Task 1: Fake REAPER item supports `delete()`

**Files:**
- Modify: `tests/fakes.py`

**Interfaces:**
- Produces: `FakeItem.delete()` (removes itself from its owning `FakeTrack.items`); `FakeTrack.add_midi_item` now tags created items with their owning track so `delete()` works.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_project.py` (near the top, after existing imports — this exercises the fake directly since it's shared test infrastructure):

```python
def test_fake_item_delete_removes_itself_from_track():
    from tests.fakes import FakeTrack

    track = FakeTrack("piano")
    item = track.add_midi_item(start=0.0, end=1.0)
    assert track.items == [item]

    item.delete()

    assert track.items == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_project.py::test_fake_item_delete_removes_itself_from_track -v`
Expected: FAIL with `AttributeError: 'FakeItem' object has no attribute 'delete'`

- [ ] **Step 3: Implement `delete()` on `FakeItem` and wire it from `FakeTrack.add_midi_item`**

In `tests/fakes.py`, replace the `FakeItem` and `FakeTrack.add_midi_item` definitions:

```python
class FakeItem:
    def __init__(self, start=0.0, end=1.0, track=None):
        self.start = start
        self.end = end
        self.active_take = FakeTake()
        self._track = track

    def delete(self):
        if self._track is not None and self in self._track.items:
            self._track.items.remove(self)
```

And in `FakeTrack`:

```python
    def add_midi_item(self, start=0.0, end=1.0):
        item = FakeItem(start=start, end=end, track=self)
        self.items.append(item)
        return item
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_project.py::test_fake_item_delete_removes_itself_from_track -v`
Expected: PASS

Also run the full suite to confirm nothing that constructs `FakeItem()` directly broke (it still works — `track` defaults to `None`):

Run: `uv run pytest tests/ -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/fakes.py tests/test_project.py
git commit -m "test: fake REAPER item supports delete() for track-clearing helpers"
```

---

## Task 2: `get_or_create_track` and `clear_track_items` in `reaper_bridge/project.py`

**Files:**
- Modify: `reaper_bridge/project.py`
- Test: `tests/test_project.py`

**Interfaces:**
- Consumes: `FakeItem.delete()` from Task 1; existing `find_track`, `create_track` in the same file.
- Produces: `get_or_create_track(project, name) -> Track` (returns existing track by exact name, or creates one); `clear_track_items(track) -> None` (deletes all MIDI items currently on the track). Both used by Task 4 (`midi.write_score_to_tracks`) and Task 5 (`curso_music21._shared.reaper_track.lesson_track`).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_project.py` (update the import line at the top to include the two new names):

```python
from reaper_bridge.project import (
    clear_track_items,
    create_track,
    find_track,
    get_or_create_track,
    list_tracks,
    rename_track,
    import_audio,
)
```

Then add:

```python
def test_get_or_create_track_returns_existing_track():
    drums = FakeTrack("bateria")
    project = FakeProject([drums])
    assert get_or_create_track(project, "bateria") is drums


def test_get_or_create_track_creates_when_missing():
    project = FakeProject([])
    track = get_or_create_track(project, "baixo")
    assert track.name == "baixo"
    assert list_tracks(project) == ["baixo"]


def test_get_or_create_track_raises_when_ambiguous():
    project = FakeProject([FakeTrack("voz"), FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="mais de uma"):
        get_or_create_track(project, "voz")


def test_clear_track_items_removes_all_items():
    project = FakeProject([FakeTrack("piano")])
    track = project.tracks[0]
    track.add_midi_item(start=0.0, end=1.0)
    track.add_midi_item(start=1.0, end=2.0)
    assert len(track.items) == 2

    clear_track_items(track)

    assert track.items == []


def test_clear_track_items_wraps_raw_exception():
    project = FakeProject([FakeTrack("piano")])
    track = project.tracks[0]

    class FailingItem:
        def delete(self):
            raise RuntimeError("REAPER disconnected")

    track.items.append(FailingItem())
    with pytest.raises(ReaperBridgeError, match="não foi possível limpar"):
        clear_track_items(track)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_project.py -v -k "get_or_create_track or clear_track_items"`
Expected: FAIL (`ImportError: cannot import name 'get_or_create_track'`)

- [ ] **Step 3: Implement both functions**

In `reaper_bridge/project.py`, add after `find_track`:

```python
def get_or_create_track(project: "reapy.Project", name: str):
    try:
        matches = [track for track in project.tracks if track.name == name]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível buscar faixas: verifique se o REAPER está aberto"
        ) from exc
    if len(matches) > 1:
        raise ReaperBridgeError(
            f"existe mais de uma faixa chamada '{name}' ({len(matches)} faixas), "
            "renomeie as faixas duplicadas antes de continuar"
        )
    if matches:
        return matches[0]
    return create_track(project, name)


def clear_track_items(track) -> None:
    try:
        for item in list(track.items):
            item.delete()
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível limpar os itens da faixa: verifique se o REAPER está aberto"
        ) from exc
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_project.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add reaper_bridge/project.py tests/test_project.py
git commit -m "feat: add get_or_create_track and clear_track_items to reaper_bridge"
```

---

## Task 3: `write_events_to_track` (variable-duration notes) in `reaper_bridge/midi.py`

**Files:**
- Modify: `reaper_bridge/midi.py`
- Test: `tests/test_midi_track.py`

**Interfaces:**
- Consumes: existing `find_track` (same file); `ReaperBridgeError`.
- Produces: `write_events_to_track(project, track_name, events, velocity=100) -> item`, where `events: list[tuple[int, float, float]]` is `(pitch_midi, start_seconds, duration_seconds)`. Used by Task 4 (`write_score_to_tracks`) and module 02/05 lessons (Tasks 8, 11).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_midi_track.py`:

```python
from reaper_bridge.midi import write_events_to_track


def test_write_events_to_track_creates_item_with_variable_durations():
    project = FakeProject([FakeTrack("piano")])
    events = [(60, 0.0, 2.0), (62, 2.0, 1.0)]

    item = write_events_to_track(project, "piano", events)

    notes = item.active_take.notes
    assert [(n.pitch, n.start, n.end) for n in notes] == [
        (60, 0.0, 2.0),
        (62, 2.0, 3.0),
    ]


def test_write_events_to_track_supports_simultaneous_notes():
    project = FakeProject([FakeTrack("piano")])
    events = [(60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0)]

    item = write_events_to_track(project, "piano", events)

    assert sorted(n.pitch for n in item.active_take.notes) == [60, 64, 67]


def test_write_events_to_track_raises_for_empty_events():
    project = FakeProject([FakeTrack("piano")])
    with pytest.raises(ReaperBridgeError, match="nenhum evento"):
        write_events_to_track(project, "piano", [])
```

(`FakeProject`, `FakeTrack`, `pytest`, `ReaperBridgeError` are already imported in this file.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_midi_track.py -v -k write_events`
Expected: FAIL (`ImportError: cannot import name 'write_events_to_track'`)

- [ ] **Step 3: Implement `write_events_to_track`**

In `reaper_bridge/midi.py`, add after `write_notes_to_track`:

```python
def write_events_to_track(
    project,
    track_name: str,
    events: list[tuple[int, float, float]],
    velocity: int = 100,
):
    if not events:
        raise ReaperBridgeError("nenhum evento para escrever no piano roll")
    track = find_track(project, track_name)
    end = max(start + duration for _, start, duration in events)
    try:
        item = track.add_midi_item(start=0.0, end=end)
        take = item.active_take
        for pitch_value, start, duration in events:
            take.add_note(
                start=start,
                end=start + duration,
                pitch=pitch_value,
                velocity=velocity,
                unit="seconds",
            )
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível escrever os eventos no piano roll: verifique se o REAPER está aberto"
        ) from exc
    return item
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_midi_track.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add reaper_bridge/midi.py tests/test_midi_track.py
git commit -m "feat: add write_events_to_track for variable-duration MIDI writing"
```

---

## Task 4: `write_score_to_tracks` (multi-part scores → multiple REAPER tracks)

**Files:**
- Modify: `reaper_bridge/midi.py` (import `get_or_create_track` from `.project`)
- Test: `tests/test_midi_score.py` (new)

**Interfaces:**
- Consumes: `get_or_create_track` (Task 2), `write_events_to_track` (Task 3), `ReaperBridgeError`.
- Produces: `write_score_to_tracks(project, score, track_prefix="", seconds_per_quarter=0.5) -> list[Track]`. `score` is any `music21.stream.Stream` (a `Score` with multiple `Part`s, a lone `Part`, or a plain `Stream`). Used by module 13 (corpus) and module 15 (capstone) in later plans — not consumed by any Fase 1 lesson, but built and tested now as shared infra.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_midi_score.py`:

```python
import pytest
from music21 import chord, note
from music21 import stream as m21stream

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import write_score_to_tracks
from reaper_bridge.project import list_tracks
from tests.fakes import FakeProject


def test_write_score_to_tracks_creates_one_track_per_part():
    score = m21stream.Score()
    soprano = m21stream.Part()
    soprano.partName = "Soprano"
    soprano.append(note.Note("C5", quarterLength=1.0))
    bass = m21stream.Part()
    bass.partName = "Baixo"
    bass.append(note.Note("C3", quarterLength=1.0))
    score.append(soprano)
    score.append(bass)
    project = FakeProject([])

    write_score_to_tracks(project, score, track_prefix="Coral - ")

    assert list_tracks(project) == ["Coral - Soprano", "Coral - Baixo"]
    soprano_notes = project.tracks[0].items[0].active_take.notes
    assert [n.pitch for n in soprano_notes] == [72]
    bass_notes = project.tracks[1].items[0].active_take.notes
    assert [n.pitch for n in bass_notes] == [48]


def test_write_score_to_tracks_expands_chords_into_simultaneous_notes():
    part = m21stream.Part()
    part.partName = "Harmonia"
    part.append(chord.Chord(["C4", "E4", "G4"], quarterLength=2.0))
    score = m21stream.Score()
    score.append(part)
    project = FakeProject([])

    write_score_to_tracks(project, score)

    notes = project.tracks[0].items[0].active_take.notes
    assert sorted(n.pitch for n in notes) == [60, 64, 67]
    assert all(n.start == 0.0 for n in notes)


def test_write_score_to_tracks_falls_back_to_single_track_for_plain_stream():
    plain = m21stream.Stream()
    plain.append(note.Note("C4", quarterLength=1.0))
    project = FakeProject([])

    write_score_to_tracks(project, plain, track_prefix="Melodia - ")

    assert list_tracks(project) == ["Melodia - parte 1"]


def test_write_score_to_tracks_raises_for_empty_score():
    empty_score = m21stream.Score()
    project = FakeProject([])
    with pytest.raises(ReaperBridgeError, match="nenhuma nota"):
        write_score_to_tracks(project, empty_score)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_midi_score.py -v`
Expected: FAIL (`ImportError: cannot import name 'write_score_to_tracks'`)

- [ ] **Step 3: Implement `write_score_to_tracks`**

In `reaper_bridge/midi.py`, change the project import line from:

```python
from .project import find_track
```

to:

```python
from .project import find_track, get_or_create_track
```

Then add, after `write_events_to_track`:

```python
def write_score_to_tracks(
    project,
    score: m21stream.Stream,
    track_prefix: str = "",
    seconds_per_quarter: float = 0.5,
):
    try:
        parts = list(score.parts)
    except AttributeError:
        parts = []
    if not parts:
        parts = [score]

    written_tracks = []
    for index, part in enumerate(parts):
        part_name = getattr(part, "partName", None) or f"parte {index + 1}"
        track_name = f"{track_prefix}{part_name}"
        events = []
        for element in part.flatten().notes:
            start = float(element.offset) * seconds_per_quarter
            duration = float(element.duration.quarterLength) * seconds_per_quarter
            for pitch_obj in element.pitches:
                events.append((pitch_obj.midi, start, duration))
        if not events:
            continue
        get_or_create_track(project, track_name)
        write_events_to_track(project, track_name, events)
        written_tracks.append(find_track(project, track_name))

    if not written_tracks:
        raise ReaperBridgeError("nenhuma nota encontrada na partitura para escrever")
    return written_tracks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_midi_score.py -v`
Expected: all PASS

Also run the full suite:

Run: `uv run pytest tests/ -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add reaper_bridge/midi.py tests/test_midi_score.py
git commit -m "feat: add write_score_to_tracks for multi-part music21 scores"
```

---

## Task 5: `curso_music21` package skeleton + `lesson_track` shared helper

**Files:**
- Create: `curso_music21/__init__.py` (empty)
- Create: `curso_music21/_shared/__init__.py` (empty)
- Create: `curso_music21/_shared/reaper_track.py`
- Create: `curso_music21/modulos/__init__.py` (empty)
- Test: `tests/test_curso_music21_shared.py` (new)

**Interfaces:**
- Consumes: `reaper_bridge.connection.get_project`, `reaper_bridge.project.get_or_create_track` (Task 2), `reaper_bridge.project.clear_track_items` (Task 2), `reaper_bridge.errors.ReaperBridgeError`.
- Produces: `lesson_track(name: str) -> tuple[Project, Track]`. Used by every `licao.py` from Task 7 onward.

- [ ] **Step 1: Create empty package files**

```bash
mkdir -p curso_music21/_shared curso_music21/modulos
touch curso_music21/__init__.py curso_music21/_shared/__init__.py curso_music21/modulos/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_curso_music21_shared.py`:

```python
from unittest.mock import patch

import pytest

from curso_music21._shared.reaper_track import lesson_track
from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import write_notes_to_track
from tests.fakes import FakeProject, FakeTrack

TRACK_NAME = "Curso 01 - Notas e Alturas"


def test_lesson_track_creates_track_when_missing():
    project = FakeProject([])
    with patch(
        "curso_music21._shared.reaper_track.get_project", return_value=project
    ):
        returned_project, track = lesson_track(TRACK_NAME)

    assert returned_project is project
    assert track.name == TRACK_NAME
    assert track in project.tracks


def test_lesson_track_clears_items_on_second_run():
    track = FakeTrack(TRACK_NAME)
    project = FakeProject([track])
    write_notes_to_track(project, TRACK_NAME, [60, 62])
    assert len(track.items) == 1

    with patch(
        "curso_music21._shared.reaper_track.get_project", return_value=project
    ):
        lesson_track(TRACK_NAME)

    assert track.items == []


def test_lesson_track_propagates_reaper_bridge_error_when_reaper_unavailable():
    with patch(
        "curso_music21._shared.reaper_track.get_project",
        side_effect=ReaperBridgeError("REAPER não está aberto"),
    ):
        with pytest.raises(ReaperBridgeError, match="não está aberto"):
            lesson_track(TRACK_NAME)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_curso_music21_shared.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'curso_music21._shared.reaper_track'`)

- [ ] **Step 4: Implement `reaper_track.py`**

Create `curso_music21/_shared/reaper_track.py`:

```python
from __future__ import annotations

import reapy

from reaper_bridge.connection import get_project
from reaper_bridge.project import clear_track_items, get_or_create_track


def lesson_track(name: str) -> tuple["reapy.Project", "reapy.Track"]:
    """Conecta ao REAPER e garante uma faixa dedicada e limpa para a lição.

    Cria a faixa se não existir; se já existir (de uma execução anterior da
    mesma lição), limpa os itens MIDI antes de devolver, para que rodar a
    lição de novo não empilhe notas repetidas.
    """
    project = get_project()
    track = get_or_create_track(project, name)
    clear_track_items(track)
    return project, track
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_curso_music21_shared.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add curso_music21/__init__.py curso_music21/_shared/__init__.py \
        curso_music21/_shared/reaper_track.py curso_music21/modulos/__init__.py \
        tests/test_curso_music21_shared.py
git commit -m "feat: add curso_music21 package skeleton and lesson_track helper"
```

---

## Task 6: Course index README

**Files:**
- Create: `curso_music21/README.md`

**Interfaces:** none (documentation only).

- [ ] **Step 1: Write the README**

Create `curso_music21/README.md`:

```markdown
# Curso de Música com music21 no piano roll do REAPER

Cada lição gera conteúdo musical com [music21](https://music21.org/music21docs/usersGuide/)
e escreve numa faixa dedicada do REAPER, para aprender vendo e ouvindo a
teoria no piano roll em vez de só ler texto.

A teoria de cada módulo combina duas referências:

- **music21 User's Guide** — como programar cada conceito.
- **[Open Music Theory](https://viva.pressbooks.pub/openmusictheory/)**
  (Creative Commons, atribuição obrigatória) — o que o conceito significa
  musicalmente. Os READMEs linkam e resumem os capítulos relevantes com
  as próprias palavras; não copiam o texto do livro.

## Pré-requisitos

1. REAPER aberto.
2. `reapy` configurado (`reapy.configure_reaper()`, rodado a partir do
   ambiente virtual do repo principal — nunca de um worktree).
3. Dependências do projeto instaladas (`uv sync`, na raiz do repositório).

## Como rodar uma lição

```bash
uv run python curso_music21/modulos/01_notas_e_alturas/licao.py
```

Cada lição escreve numa faixa própria (`Curso NN - <nome>`), criando-a se
não existir e limpando notas de uma execução anterior antes de escrever de
novo — pode rodar a mesma lição quantas vezes quiser.

## Módulos (Fase 1)

| # | Módulo |
|---|---|
| 01 | Notas e Alturas |
| 02 | Ritmo: Durações e Compassos |
| 03 | Escalas e Tonalidades |
| 04 | Intervalos |
| 05 | Acordes e Tríades |

O currículo completo (16 módulos, incluindo harmonia funcional, condução
de vozes, contraponto, forma, corpus/análise e o capstone de composição e
arranjo multi-instrumental) está descrito em
`docs/superpowers/specs/2026-09-27-curso-music21-design.md`; os módulos
06-16 chegam em fases de implementação seguintes.
```

- [ ] **Step 2: Commit**

```bash
git add curso_music21/README.md
git commit -m "docs: add curso_music21 course index README"
```

---

## Task 7: Módulo 01 — Notas e Alturas

**Files:**
- Create: `curso_music21/modulos/01_notas_e_alturas/__init__.py` (empty)
- Create: `curso_music21/modulos/01_notas_e_alturas/README.md`
- Create: `curso_music21/modulos/01_notas_e_alturas/licao.py`
- Create: `tests/test_curso_music21_licoes.py` (new — will grow in Tasks 8-11)

**Interfaces:**
- Consumes: `curso_music21._shared.reaper_track.lesson_track` (Task 5), `reaper_bridge.midi.write_notes_to_track` (existing), `reaper_bridge.errors.ReaperBridgeError`.
- Produces: `build_pitches() -> list[int]` in this module, imported by its test via `importlib.import_module("curso_music21.modulos.01_notas_e_alturas.licao")`.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/01_notas_e_alturas
touch curso_music21/modulos/01_notas_e_alturas/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_curso_music21_licoes.py`:

```python
import importlib

MODULO_01 = "curso_music21.modulos.01_notas_e_alturas.licao"


def test_modulo_01_build_pitches_same_class_then_different_classes():
    licao = importlib.import_module(MODULO_01)
    assert licao.build_pitches() == [36, 48, 60, 72, 60, 62, 64, 65, 67, 69, 71]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/01_notas_e_alturas/README.md`:

```markdown
# 01 — Notas e Alturas

**Referências:** music21 User's Guide, caps. 2-3 ("Notes"; "Pitches,
Durations, and Notes again") · Open Music Theory, capítulo "Pitch and
Pitch Class" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma **altura** (pitch) é uma nota específica (ex.: C4 = Dó central). Uma
**classe de nota** (pitch class) ignora a oitava: C2, C3, C4 e C5 são
alturas diferentes, mas todas pertencem à mesma classe "Dó". Em seguida,
notas com nomes diferentes (Dó, Ré, Mi...) na mesma oitava são classes de
nota diferentes.

## O que o script faz

`build_pitches()` gera duas sequências:

1. A nota Dó em quatro oitavas (2 a 5) — mesma classe, alturas diferentes.
2. As sete notas naturais (Dó a Si) na 4ª oitava — classes diferentes.

## O que esperar no piano roll

Na faixa "Curso 01 - Notas e Alturas": quatro notas na mesma posição
vertical relativa (mesma letra, oitavas diferentes, saltando de 12 em 12
semitons), seguidas de sete notas subindo em posições diferentes.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/01_notas_e_alturas/licao.py`:

```python
"""Lição 01 - Notas e Alturas."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import pitch  # noqa: E402

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_notes_to_track  # noqa: E402

TRACK_NAME = "Curso 01 - Notas e Alturas"


def build_pitches() -> list[int]:
    """C em quatro oitavas (mesma classe de nota, alturas diferentes),
    seguido dos nomes de nota de Do a Si numa só oitava (classes diferentes)."""
    same_pitch_class = [pitch.Pitch(f"C{octave}").midi for octave in range(2, 6)]
    different_pitch_classes = [
        pitch.Pitch(f"{name}4").midi for name in ["C", "D", "E", "F", "G", "A", "B"]
    ]
    return same_pitch_class + different_pitch_classes


def main() -> None:
    pitches = build_pitches()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_notes_to_track(project, TRACK_NAME, pitches, note_length=0.5)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(f"Confira a faixa '{TRACK_NAME}' no piano roll do REAPER.")
    print(
        "As quatro primeiras notas são todas 'Do' (C) em oitavas diferentes "
        "-- mesma classe de nota. As sete seguintes são notas diferentes na "
        "mesma oitava."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/01_notas_e_alturas tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 01 - notas e alturas"
```

---

## Task 8: Módulo 02 — Ritmo: Durações e Compassos

**Files:**
- Create: `curso_music21/modulos/02_ritmo_duracoes_e_compassos/__init__.py` (empty)
- Create: `curso_music21/modulos/02_ritmo_duracoes_e_compassos/README.md`
- Create: `curso_music21/modulos/02_ritmo_duracoes_e_compassos/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track` (Task 5), `write_events_to_track` (Task 3), `ReaperBridgeError`.
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/02_ritmo_duracoes_e_compassos
touch curso_music21/modulos/02_ritmo_duracoes_e_compassos/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_02 = "curso_music21.modulos.02_ritmo_duracoes_e_compassos.licao"


def test_modulo_02_build_events_halves_duration_each_step():
    licao = importlib.import_module(MODULO_02)
    assert licao.build_events() == [
        (60, 0.0, 2.0),
        (60, 2.0, 1.0),
        (60, 3.0, 0.5),
        (60, 3.5, 0.25),
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_02`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/02_ritmo_duracoes_e_compassos/README.md`:

```markdown
# 02 — Ritmo: Durações e Compassos

**Referências:** music21 User's Guide, caps. 3 (cont.), 14, 19, 27
("Time Signatures and Beats"; "Advanced Durations"; "Grace Notes") · Open
Music Theory, capítulos "Duration & Rhythm" e "Meter"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Duração é quanto tempo uma nota soa, medida em figuras (semibreve, mínima,
semínima, colcheia...), cada uma valendo metade da anterior. Isso é
independente da altura da nota — por isso este módulo usa sempre a mesma
nota (Dó4), variando só a duração.

## O que o script faz

`build_events()` gera quatro eventos `(altura, início, duração)` na mesma
altura, cada um com metade da duração do anterior: semibreve (4 tempos),
mínima (2), semínima (1), colcheia (0.5) — a 120 bpm (0.5s por tempo).

## O que esperar no piano roll

Quatro blocos na mesma linha vertical (mesma altura), cada um com metade
da largura do anterior.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/02_ritmo_duracoes_e_compassos/licao.py`:

```python
"""Lição 02 - Ritmo: Durações e Compassos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 02 - Ritmo: Duracoes e Compassos"
SECONDS_PER_QUARTER = 0.5  # 120 bpm


def build_events() -> list[tuple[int, float, float]]:
    """Semibreve, mínima, semínima e colcheia em sequência, todas na mesma
    altura (C4), para comparar duração sem a variável de altura mudando."""
    quarter_lengths = [4.0, 2.0, 1.0, 0.5]
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for quarter_length in quarter_lengths:
        duration = quarter_length * SECONDS_PER_QUARTER
        events.append((60, start, duration))
        start += duration
    return events


def main() -> None:
    events = build_events()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_events_to_track(project, TRACK_NAME, events)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(f"Confira a faixa '{TRACK_NAME}' no piano roll do REAPER.")
    print(
        "Quatro notas na mesma altura, cada uma com metade da duração da "
        "anterior: semibreve, mínima, semínima, colcheia."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/02_ritmo_duracoes_e_compassos tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 02 - ritmo: duracoes e compassos"
```

---

## Task 9: Módulo 03 — Escalas e Tonalidades

**Files:**
- Create: `curso_music21/modulos/03_escalas_e_tonalidades/__init__.py` (empty)
- Create: `curso_music21/modulos/03_escalas_e_tonalidades/README.md`
- Create: `curso_music21/modulos/03_escalas_e_tonalidades/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track` (Task 5), `reaper_bridge.midi.generate_scale` (existing), `reaper_bridge.midi.write_notes_to_track` (existing), `ReaperBridgeError`.
- Produces: `build_pitches() -> list[int]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/03_escalas_e_tonalidades
touch curso_music21/modulos/03_escalas_e_tonalidades/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_03 = "curso_music21.modulos.03_escalas_e_tonalidades.licao"


def test_modulo_03_build_pitches_c_major_then_a_natural_minor():
    licao = importlib.import_module(MODULO_03)
    assert licao.build_pitches() == [
        48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72,
        57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81,
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_03`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/03_escalas_e_tonalidades/README.md`:

```markdown
# 03 — Escalas e Tonalidades

**Referências:** `reaper_bridge.midi.generate_scale` (já existente) · Open
Music Theory, capítulo "Major and Minor Scales"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma tonalidade (key) é organizada em torno de uma escala. Dó maior e Lá
menor natural são **relativas**: usam exatamente as mesmas sete notas,
mas soam diferente porque começam (e resolvem) em graus diferentes.

## O que o script faz

`build_pitches()` toca a escala de Dó maior completa e, em seguida, a
escala de Lá menor natural completa, usando `generate_scale` (já usado
pelo MCP server do reaper-copilot).

## O que esperar no piano roll

Duas subidas de escala consecutivas, cobrindo as mesmas sete posições
verticais (mesmas notas), começando em pontos diferentes.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/03_escalas_e_tonalidades/licao.py`:

```python
"""Lição 03 - Escalas e Tonalidades."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_scale, write_notes_to_track  # noqa: E402

TRACK_NAME = "Curso 03 - Escalas e Tonalidades"


def build_pitches() -> list[int]:
    """Escala de Do maior seguida da escala de La menor natural (relativa) --
    mesmas notas, tonalidades diferentes."""
    return generate_scale("C", "major") + generate_scale("A", "natural_minor")


def main() -> None:
    pitches = build_pitches()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_notes_to_track(project, TRACK_NAME, pitches, note_length=0.25)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(f"Confira a faixa '{TRACK_NAME}' no piano roll do REAPER.")
    print(
        "Primeira metade: escala de Do maior. Segunda metade: escala de La "
        "menor natural -- mesmas sete notas, tonalidades diferentes."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/03_escalas_e_tonalidades tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 03 - escalas e tonalidades"
```

---

## Task 10: Módulo 04 — Intervalos

**Files:**
- Create: `curso_music21/modulos/04_intervalos/__init__.py` (empty)
- Create: `curso_music21/modulos/04_intervalos/README.md`
- Create: `curso_music21/modulos/04_intervalos/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track` (Task 5), `write_notes_to_track` (existing), `ReaperBridgeError`, `music21.interval.Interval`, `music21.pitch.Pitch`.
- Produces: `build_pitches() -> list[int]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/04_intervalos
touch curso_music21/modulos/04_intervalos/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_04 = "curso_music21.modulos.04_intervalos.licao"


def test_modulo_04_build_pitches_root_then_each_interval():
    licao = importlib.import_module(MODULO_04)
    assert licao.build_pitches() == [60, 60, 64, 67, 72]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_04`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/04_intervalos/README.md`:

```markdown
# 04 — Intervalos

**Referências:** music21 User's Guide, cap. 18 ("Intervals") · Open Music
Theory, capítulo "Intervals" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Um intervalo é a distância entre duas notas. `P1` (uníssono, distância
zero), `M3` (terça maior), `P5` (quinta justa) e `P8` (oitava) são os
intervalos que formam a base da tríade maior e da relação de oitava.

## O que o script faz

`build_pitches()` toca a nota Dó4 (fundamental), e depois cada intervalo
(`P1`, `M3`, `P5`, `P8`) aplicado sobre essa mesma fundamental, usando
`music21.interval.Interval.transposePitch`.

## O que esperar no piano roll

A mesma nota repetida (fundamental, depois uníssono), seguida de três
notas subindo — terça, quinta e oitava acima da fundamental.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/04_intervalos/licao.py`:

```python
"""Lição 04 - Intervalos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import interval, pitch  # noqa: E402

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_notes_to_track  # noqa: E402

TRACK_NAME = "Curso 04 - Intervalos"
INTERVALOS = ["P1", "M3", "P5", "P8"]


def build_pitches() -> list[int]:
    """Nota fundamental seguida de cada intervalo aplicado sobre ela, para
    ouvir a distância entre eles."""
    root = pitch.Pitch("C4")
    pitches = [root.midi]
    for name in INTERVALOS:
        iv = interval.Interval(name)
        pitches.append(iv.transposePitch(root).midi)
    return pitches


def main() -> None:
    pitches = build_pitches()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_notes_to_track(project, TRACK_NAME, pitches, note_length=0.5)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(f"Confira a faixa '{TRACK_NAME}' no piano roll do REAPER.")
    print(
        "Fundamental, uníssono (mesma nota), terça maior, quinta justa e "
        "oitava -- todos acima da mesma fundamental (Do4)."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/04_intervalos tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 04 - intervalos"
```

---

## Task 11: Módulo 05 — Acordes e Tríades

**Files:**
- Create: `curso_music21/modulos/05_acordes_e_triades/__init__.py` (empty)
- Create: `curso_music21/modulos/05_acordes_e_triades/README.md`
- Create: `curso_music21/modulos/05_acordes_e_triades/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track` (Task 5), `reaper_bridge.midi.generate_chord` (existing), `write_events_to_track` (Task 3), `ReaperBridgeError`.
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/05_acordes_e_triades
touch curso_music21/modulos/05_acordes_e_triades/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_05 = "curso_music21.modulos.05_acordes_e_triades.licao"


def test_modulo_05_build_events_four_triad_qualities_on_same_root():
    licao = importlib.import_module(MODULO_05)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (60, 1.0, 1.0), (63, 1.0, 1.0), (67, 1.0, 1.0),
        (60, 2.0, 1.0), (63, 2.0, 1.0), (66, 2.0, 1.0),
        (60, 3.0, 1.0), (64, 3.0, 1.0), (68, 3.0, 1.0),
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_05`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/05_acordes_e_triades/README.md`:

```markdown
# 05 — Acordes e Tríades

**Referências:** music21 User's Guide, caps. 7, 9 ("Chords"; "Chordify") ·
Open Music Theory, capítulo "Triads and Seventh Chords"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma tríade é um acorde de três notas empilhadas em terças. As quatro
qualidades básicas (maior, menor, diminuta, aumentada) usam a mesma
fundamental mas intervalos internos diferentes, o que muda completamente
o caráter do acorde.

## O que o script faz

`build_events()` toca, em sequência, as tríades maior, menor, diminuta e
aumentada sobre a mesma fundamental (Dó), usando `generate_chord` (já
existente) e `write_events_to_track` para tocar as três notas de cada
acorde simultaneamente.

## O que esperar no piano roll

Quatro blocos de três notas empilhadas, um após o outro, todos começando
na mesma nota (Dó) mas com as outras duas notas em posições ligeiramente
diferentes a cada bloco.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/05_acordes_e_triades/licao.py`:

```python
"""Lição 05 - Acordes e Tríades."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_chord, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 05 - Acordes e Triades"
QUALIDADES = ["major", "minor", "diminished", "augmented"]


def build_events() -> list[tuple[int, float, float]]:
    """As quatro tríades clássicas sobre a mesma fundamental (Do), uma de
    cada vez, para comparar a qualidade do acorde."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    duration = 1.0
    for quality in QUALIDADES:
        for pitch_value in generate_chord(60, quality):
            events.append((pitch_value, start, duration))
        start += duration
    return events


def main() -> None:
    events = build_events()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_events_to_track(project, TRACK_NAME, events)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(f"Confira a faixa '{TRACK_NAME}' no piano roll do REAPER.")
    print(
        "Quatro tríades sobre Do: maior, menor, diminuta, aumentada -- "
        "compare como a terça e a quinta mudam de posição a cada uma."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS

Also run the entire suite to confirm Fase 1 is fully green:

Run: `uv run pytest tests/ -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/05_acordes_e_triades tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 05 - acordes e triades"
```

---

## After this plan

Fase 1 delivers working, testable infrastructure plus 5 runnable lessons.
Módulos 06-16 (harmonia funcional, cadências, notas de adorno, dominantes
secundárias, condução de vozes, contraponto, forma, corpus/Bach, harmonia
popular, e o capstone de composição e arranjo multi-instrumental) get
their own plan(s) later, following this same task shape, per the spec's
"Ordem de entrega" section.
