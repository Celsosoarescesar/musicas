# Curso music21 no piano roll — Fase 4 (módulo 13: música real — corpus e análise) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two known bugs in `write_score_to_tracks` (built in Fase 1, unused since, both flagged in Fase 1's final review as prerequisites for this exact phase), then add módulo 13 (Música Real: Corpus e Análise) — the course's first lesson built from real, pre-existing music (a Bach chorale from music21's bundled corpus) instead of programmatically generated content.

**Architecture:** This is the first phase since Fase 1 that touches `reaper_bridge`. Task 1 fixes `write_score_to_tracks` (`reaper_bridge/midi.py`) so it (a) clears a track's existing items before rewriting — making it idempotent, matching `lesson_track`'s existing idempotency guarantee — and (b) de-duplicates track names when two parts share a `partName`, appending `" ({index+1})"` on collision instead of silently merging both parts' notes onto one track. Task 2 builds módulo 13: it loads a real Bach chorale (`bach/bwv66.6`) via `music21.corpus.parse`, takes its first two measures (SATB, four voices), writes each voice to its own REAPER track via the now-fixed `write_score_to_tracks`, and demonstrates two more corpus-search capabilities from the spec (automatic key detection via `Score.analyze("key")`, and a corpus-wide search via `music21.corpus.search`) that were not yet used anywhere in the course.

**Tech Stack:** Python 3.11, music21 10.5.0 (`music21.corpus` — bundled, fully offline, no network access — used directly for the first time in this course), reapy, pytest, `tests/fakes.py`.

**Spec:** `docs/superpowers/specs/2026-09-27-curso-music21-design.md`

## Global Constraints

- Every `licao.py` separates pure `build_*()` functions (no REAPER/reapy call) from `main()` (the only part doing I/O). Módulo 13's `build_excerto()`/`build_tonalidade_detectada()`/`build_total_corais_bach()` call `music21.corpus.parse`/`.analyze`/`corpus.search`, which read music21's own bundled local data files — this is music21's normal operation, not REAPER I/O, and is consistent with "pure" as used throughout this course (testable without REAPER open).
- `main()` must catch `ReaperBridgeError` and print a friendly Portuguese message, never let a raw traceback surface.
- `curso_music21/modulos/NN_xxx` directory names start with digits, so tests import them with `importlib.import_module("curso_music21.modulos.NN_xxx.licao")`, never a `from x.y import z` statement.
- Task 2 must APPEND to the existing `tests/test_curso_music21_licoes.py` (holds módulos 01-12) without disturbing its existing tests.
- **Exception to Fases 2-3's "zero new `reaper_bridge` code" pattern:** this phase's Task 1 modifies `reaper_bridge/midi.py` and `reaper_bridge/project.py` imports — this is deliberate, fixing pre-existing, already-flagged bugs in shared library code, not course-specific logic. Task 1 must land, reviewed and merged into this branch, before Task 2 starts, since Task 2 depends on the fix.
- Track names for módulo 13 (`"Curso 13 - Soprano"`, `"Curso 13 - Alto"`, `"Curso 13 - Tenor"`, `"Curso 13 - Bass"`) must be distinct from every track name registered by módulos 01-12.
- Every literal value in this plan (note/offset/duration/pitch data for the Bach excerpt, the detected key, the corpus search count threshold) was verified by directly executing the equivalent code against the real installed music21 10.5.0 and its bundled corpus before this plan was written — they are exact, not estimates. The corpus search count uses a `>=` threshold (not an exact pinned number) deliberately: the exact corpus size is a music21-library implementation detail that could shift with a future music21 upgrade unrelated to this course, and the lesson's point ("there are many more chorales to explore") only needs "a lot," not an exact count.

## Review Focus

- `write_score_to_tracks`'s fix must call `clear_track_items` on a track it just got via `get_or_create_track`, before writing new events — not after, and not skip it for either branch (existing track or newly-created track; a newly-created track has no items, so clearing it is a harmless no-op, but the code must not special-case around calling it).
- `write_score_to_tracks`'s dedup fix must produce genuinely distinct REAPER track names when two parts share a `partName` (not overwrite/merge one part's notes into the other's track) — verified via a real two-part collision test, not just reasoned about.
- Módulo 13's `build_excerto()` must return the exact SATB note data verified against the real Bach chorale (offsets, durations, MIDI pitches for all four voices) — a transcription slip here is the single largest literal value in this plan (34 notes across 4 voices).
- Módulo 13's `main()` must call `write_score_to_tracks` (not `write_events_to_track`/`write_notes_to_track` directly) — it's the only lesson in the course writing from a `music21.stream.Score` rather than a hand-built pitch/event list, and it doesn't go through `lesson_track()` (which only handles one track) — it calls `reaper_bridge.connection.get_project()` directly instead, matching `write_score_to_tracks`'s own signature (`project` as a parameter, not a track name).
- `build_total_corais_bach()` must call the real `music21.corpus.search(...)` and return its actual length — not a hardcoded number that happens to satisfy the test's `>=` threshold.

---

## Task 1: Fix `write_score_to_tracks` — idempotency + duplicate-partName dedup

**Files:**
- Modify: `reaper_bridge/midi.py`
- Modify: `tests/test_midi_score.py`

**Interfaces:**
- Consumes: `reaper_bridge.project.clear_track_items` (existing, built in Fase 1 Task 2, already tested) — newly imported into `midi.py` alongside the already-imported `find_track`/`get_or_create_track`.
- Produces: `write_score_to_tracks(project, score, track_prefix="", seconds_per_quarter=0.5) -> list[Track]` — same signature as before, now idempotent and collision-safe. Consumed by Task 2's módulo 13.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_midi_score.py` (the file already imports `pytest`, `chord`, `note`, `m21stream`, `ReaperBridgeError`, `write_score_to_tracks`, `list_tracks`, `FakeProject` — no new imports needed):

```python
def test_write_score_to_tracks_is_idempotent_on_rerun():
    score = m21stream.Score()
    part = m21stream.Part()
    part.partName = "Melodia"
    part.append(note.Note("C4", quarterLength=1.0))
    part.append(note.Note("D4", quarterLength=1.0))
    score.append(part)
    project = FakeProject([])

    write_score_to_tracks(project, score)
    write_score_to_tracks(project, score)

    track = project.tracks[0]
    assert len(track.items) == 1
    assert [n.pitch for n in track.items[0].active_take.notes] == [60, 62]


def test_write_score_to_tracks_dedupes_repeated_part_names():
    score = m21stream.Score()
    part1 = m21stream.Part()
    part1.partName = "Voz"
    part1.append(note.Note("C4", quarterLength=1.0))
    part2 = m21stream.Part()
    part2.partName = "Voz"
    part2.append(note.Note("G4", quarterLength=1.0))
    score.append(part1)
    score.append(part2)
    project = FakeProject([])

    write_score_to_tracks(project, score)

    assert list_tracks(project) == ["Voz", "Voz (2)"]
    assert [n.pitch for n in project.tracks[0].items[0].active_take.notes] == [60]
    assert [n.pitch for n in project.tracks[1].items[0].active_take.notes] == [67]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_midi_score.py -v -k "idempotent or dedupes"`
Expected: FAIL — the idempotency test fails because the second run leaves `len(track.items) == 2`; the dedup test fails because both parts collapse onto one track named `"Voz"` (the second `get_or_create_track` call finds the existing "Voz" track instead of creating a distinct one).

- [ ] **Step 3: Fix `write_score_to_tracks`**

In `reaper_bridge/midi.py`, change the project import line from:

```python
from .project import find_track, get_or_create_track
```

to:

```python
from .project import clear_track_items, find_track, get_or_create_track
```

Then replace the body of `write_score_to_tracks`:

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
    used_names: set[str] = set()
    for index, part in enumerate(parts):
        part_name = getattr(part, "partName", None) or f"parte {index + 1}"
        track_name = f"{track_prefix}{part_name}"
        if track_name in used_names:
            track_name = f"{track_name} ({index + 1})"
        used_names.add(track_name)
        events = []
        for element in part.flatten().notes:
            start = float(element.offset) * seconds_per_quarter
            duration = float(element.duration.quarterLength) * seconds_per_quarter
            for pitch_obj in element.pitches:
                events.append((pitch_obj.midi, start, duration))
        if not events:
            continue
        track = get_or_create_track(project, track_name)
        clear_track_items(track)
        write_events_to_track(project, track_name, events)
        written_tracks.append(find_track(project, track_name))

    if not written_tracks:
        raise ReaperBridgeError("nenhuma nota encontrada na partitura para escrever")
    return written_tracks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_midi_score.py -v`
Expected: all PASS (including the pre-existing tests from Fase 1 — multi-part score, chord expansion, plain-Stream fallback, empty-score error — none of which exercised idempotency or name collision, so none should have been affected by this fix)

Also run the full suite:

Run: `uv run pytest tests/ -q`
Expected: all PASS (206 baseline + 2 new = 208)

- [ ] **Step 5: Commit**

```bash
git add reaper_bridge/midi.py tests/test_midi_score.py
git commit -m "fix: write_score_to_tracks is idempotent and dedupes repeated part names"
```

---

## Task 2: Módulo 13 — Música Real: Corpus e Análise

**Files:**
- Create: `curso_music21/modulos/13_musica_real_corpus_e_analise/__init__.py` (empty)
- Create: `curso_music21/modulos/13_musica_real_corpus_e_analise/README.md`
- Create: `curso_music21/modulos/13_musica_real_corpus_e_analise/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `reaper_bridge.connection.get_project` (existing), `reaper_bridge.midi.write_score_to_tracks` (existing, fixed in Task 1), `reaper_bridge.errors.ReaperBridgeError`, `music21.corpus.parse`, `music21.corpus.search`.
- Produces: `build_excerto() -> music21.stream.Score`, `build_tonalidade_detectada() -> str`, `build_total_corais_bach() -> int` in this module, imported by tests via `importlib.import_module("curso_music21.modulos.13_musica_real_corpus_e_analise.licao")`.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/13_musica_real_corpus_e_analise
touch curso_music21/modulos/13_musica_real_corpus_e_analise/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_13 = "curso_music21.modulos.13_musica_real_corpus_e_analise.licao"


def test_modulo_13_build_excerto_satb_com_notas_do_coral_de_bach():
    licao = importlib.import_module(MODULO_13)
    excerto = licao.build_excerto()
    dados = {
        part.partName: [
            (round(n.offset, 2), n.duration.quarterLength, n.pitch.midi)
            for n in part.flatten().notes
        ]
        for part in excerto.parts
    }
    assert dados == {
        "Soprano": [
            (0.0, 1.0, 69), (1.0, 1.0, 71), (2.0, 1.0, 73), (3.0, 1.0, 76),
            (4.0, 1.0, 73), (5.0, 1.0, 71), (6.0, 1.0, 69), (7.0, 1.0, 73),
        ],
        "Alto": [
            (0.0, 1.0, 66), (1.0, 1.0, 64), (2.0, 1.0, 64), (3.0, 1.0, 64),
            (4.0, 0.5, 64), (4.5, 0.5, 69), (5.0, 1.0, 68), (6.0, 1.0, 64),
            (7.0, 1.0, 68),
        ],
        "Tenor": [
            (0.0, 1.0, 61), (1.0, 1.0, 59), (2.0, 1.0, 57), (3.0, 1.0, 59),
            (4.0, 0.5, 57), (4.5, 0.5, 64), (5.0, 0.5, 64), (5.5, 0.5, 62),
            (6.0, 1.0, 61), (7.0, 1.0, 61),
        ],
        "Bass": [
            (0.0, 1.0, 54), (1.0, 1.0, 56), (2.0, 1.0, 57), (3.0, 1.0, 56),
            (4.0, 0.5, 57), (4.5, 0.5, 49), (5.0, 1.0, 52), (6.0, 1.0, 45),
            (7.0, 1.0, 53),
        ],
    }


def test_modulo_13_build_tonalidade_detectada_confirma_la_maior():
    licao = importlib.import_module(MODULO_13)
    assert licao.build_tonalidade_detectada() == "A major"


def test_modulo_13_build_total_corais_bach_encontra_pelo_menos_cem():
    licao = importlib.import_module(MODULO_13)
    assert licao.build_total_corais_bach() >= 100
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_13`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/13_musica_real_corpus_e_analise/README.md`:

```markdown
# 13 — Música Real: Corpus e Análise

**Referências:** music21 User's Guide, caps. 11, 53 ("Corpus Searching";
"Advanced Corpus and Metadata Searching") · corpus de corais de Bach
embutido no music21 (offline, sem acesso à internet).

## Teoria

Até aqui, todo o material foi gerado programaticamente. Este módulo usa
o corpus embutido do music21 — centenas de partituras prontas, incluindo
uma quantidade grande de corais a quatro vozes de Bach — para trabalhar
com música real. As quatro vozes (Soprano, Alto, Tenor, Baixo) são
exatamente o tipo de condução de vozes e contraponto estudado nos
módulos 10 e 11, só que escritas por Bach.

## O que o script faz

Carrega o coral BWV 66.6 do corpus (`music21.corpus.parse`), recorta a
primeira frase (dois compassos), escreve cada voz numa faixa separada do
REAPER (`write_score_to_tracks`, agora corrigido para limpar a faixa
antes de reescrever e evitar colisão de nomes entre vozes), detecta a
tonalidade automaticamente e conta quantos corais de Bach existem no
corpus.

## O que esperar no piano roll

Quatro faixas (Soprano, Alto, Tenor, Baixo), cada uma com uma linha
melódica real de Bach, tocando juntas — a primeira frase do coral.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/13_musica_real_corpus_e_analise/licao.py`:

```python
"""Lição 13 - Música Real: Corpus e Análise."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import corpus, stream as m21stream  # noqa: E402

from reaper_bridge.connection import get_project  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_score_to_tracks  # noqa: E402

TRACK_PREFIX = "Curso 13 - "
CORAL = "bach/bwv66.6"


def build_excerto() -> m21stream.Score:
    """Carrega o coral BWV 66.6 de Bach do corpus embutido do music21 e
    recorta os dois primeiros compassos (a primeira frase)."""
    partitura = corpus.parse(CORAL)
    return partitura.measures(1, 2)


def build_tonalidade_detectada() -> str:
    """Usa a análise automática de tonalidade do music21 sobre o trecho
    -- confirma que é Lá maior sem precisar informar a tonalidade."""
    excerto = build_excerto()
    tonalidade = excerto.analyze("key")
    return f"{tonalidade.tonic.name} {tonalidade.mode}"


def build_total_corais_bach() -> int:
    """Conta quantos corais de Bach existem no corpus embutido do
    music21 -- mostra que há muito mais pra explorar além dessa peça."""
    return len(corpus.search("bach", field="composer"))


def main() -> None:
    excerto = build_excerto()
    tonalidade = build_tonalidade_detectada()
    total_corais = build_total_corais_bach()
    try:
        project = get_project()
        write_score_to_tracks(project, excerto, track_prefix=TRACK_PREFIX)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(
        f"Confira as faixas '{TRACK_PREFIX}Soprano', '{TRACK_PREFIX}Alto', "
        f"'{TRACK_PREFIX}Tenor' e '{TRACK_PREFIX}Bass' no piano roll do REAPER."
    )
    print(f"Tonalidade detectada automaticamente: {tonalidade}.")
    print(
        f"Esse coral é um entre pelo menos {total_corais} corais de Bach "
        "disponíveis no corpus do music21 -- experimente trocar CORAL por "
        "outro (ex: 'bach/bwv1.6') para explorar mais."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (módulos 01-13)

Also run the entire suite to confirm Fase 4 is fully green:

Run: `uv run pytest tests/ -v`
Expected: all PASS (208 from Task 1 + 3 new = 211)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/13_musica_real_corpus_e_analise tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 13 - musica real: corpus e analise"
```

---

## After this plan

Fase 4 delivers módulo 13 and fixes the last piece of prerequisite debt
flagged since Fase 1. Módulo 14 (Harmonia Popular / Cifras e Acordes
Estendidos) is next, followed by the módulo 15 capstone (multi-instrument
composition/arrangement) and módulo 16 (bonus, post-tonal) — the final
two phases of the spec's "Ordem de entrega."
