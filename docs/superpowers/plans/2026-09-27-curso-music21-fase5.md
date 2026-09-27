# Curso music21 no piano roll — Fase 5 (módulo 14: harmonia popular) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add módulo 14 (Harmonia Popular / Cifras e Acordes Estendidos) to the music21-in-REAPER-piano-roll course, continuing directly from Fases 1-4 (already merged to master).

**Architecture:** Like Fases 2 and 3, this phase needs **no new `reaper_bridge` code**. `generate_progression` (built in Fase 1) already handles seventh- and ninth-chord Roman-numeral figures natively — `music21.roman.RomanNumeral` parses figures like `"ii7"`, `"V7"`, `"IMaj7"`, `"ii9"`, `"V9"`, `"IM9"` out of the box, verified live before this plan was written. The single lesson reuses `generate_progression` + `write_events_to_track`, exactly like módulos 06/07/09/12.

**Tech Stack:** Python 3.11, music21 10.5.0, reapy, pytest, `tests/fakes.py`.

**Spec:** `docs/superpowers/specs/2026-09-27-curso-music21-design.md`

## Global Constraints

- `licao.py` separates a pure `build_events()` function (music21 only, no REAPER — unit-testable without REAPER open) from `main()` (the only part doing I/O).
- `main()` must catch `ReaperBridgeError` and print a friendly Portuguese message, never let a raw traceback surface.
- Reuses existing `generate_progression` and `write_events_to_track` — zero new `reaper_bridge` code this phase.
- `curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos` starts with a digit, so tests import it with `importlib.import_module("curso_music21.modulos.14_harmonia_popular_cifras_e_acordes_estendidos.licao")`, never a `from x.y import z` statement.
- Must APPEND to the existing `tests/test_curso_music21_licoes.py` (holds módulos 01-13) without disturbing its existing tests.
- Track name (`"Curso 14 - Harmonia Popular (Cifras e Acordes Estendidos)"`) must be distinct from every track name registered by módulos 01-13.
- The event list in this plan (27 events: two 3-chord groups, one of seventh chords and one of ninth chords, separated by a gap) was verified by directly executing `generate_progression("C", ["ii7","V7","IMaj7"])` and `generate_progression("C", ["ii9","V9","IM9"])` against the real installed music21 10.5.0 before this plan was written — exact, not estimated.

## Review Focus

- `build_events()` must exactly match this plan's verified 27-event literal list — the two chord groups (7ths, then 9ths) each have 3 chords of increasing note-count (4 notes for sevenths, 5 for ninths), a common place for an off-by-one or copy-paste slip.
- `build_events()` must call `generate_progression` with the seventh/ninth-chord figure strings (`"ii7"`, `"V7"`, `"IMaj7"`, `"ii9"`, `"V9"`, `"IM9"`) rather than reimplementing chord-interval math — this is the whole point of the lesson (reusing existing, tested infrastructure with richer Roman-numeral figures).
- The gap between the two chord groups (0.5s, after the third seventh-chord ends at 3.0, so the ninth-chord group starts at 3.5) must be correct — verified against the literal list, not just "a gap exists."
- Track name distinctness across all 14 registered track-name strings (módulos 01-14).
- `build_events()` must stay free of any REAPER/reapy import or call.

---

## Task 1: Módulo 14 — Harmonia Popular (Cifras e Acordes Estendidos)

**Files:**
- Create: `curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos/__init__.py` (empty)
- Create: `curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos/README.md`
- Create: `curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `curso_music21._shared.reaper_track.lesson_track` (existing), `reaper_bridge.midi.generate_progression` and `reaper_bridge.midi.write_events_to_track` (existing), `reaper_bridge.errors.ReaperBridgeError`.
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module, imported by its test via `importlib.import_module("curso_music21.modulos.14_harmonia_popular_cifras_e_acordes_estendidos.licao")`.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos
touch curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_14 = "curso_music21.modulos.14_harmonia_popular_cifras_e_acordes_estendidos.licao"


def test_modulo_14_build_events_setimas_depois_nonas():
    licao = importlib.import_module(MODULO_14)
    assert licao.build_events() == [
        (62, 0.0, 1.0), (65, 0.0, 1.0), (69, 0.0, 1.0), (72, 0.0, 1.0),
        (67, 1.0, 1.0), (71, 1.0, 1.0), (74, 1.0, 1.0), (77, 1.0, 1.0),
        (60, 2.0, 1.0), (64, 2.0, 1.0), (67, 2.0, 1.0), (71, 2.0, 1.0),
        (62, 3.5, 1.0), (65, 3.5, 1.0), (69, 3.5, 1.0), (72, 3.5, 1.0), (76, 3.5, 1.0),
        (67, 4.5, 1.0), (71, 4.5, 1.0), (74, 4.5, 1.0), (77, 4.5, 1.0), (81, 4.5, 1.0),
        (60, 5.5, 1.0), (64, 5.5, 1.0), (67, 5.5, 1.0), (71, 5.5, 1.0), (74, 5.5, 1.0),
    ]
```

This pins `generate_progression("C", ["ii7", "V7", "IMaj7"])` producing
`[[62,65,69,72], [67,71,74,77], [60,64,67,71]]` (Dm7-G7-Cmaj7, the classic
jazz turnaround) and `generate_progression("C", ["ii9", "V9", "IM9"])`
producing `[[62,65,69,72,76], [67,71,74,77,81], [60,64,67,71,74]]` (the
same three chords with an added 9th each) — verified live against
music21 before this plan was written.

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_14`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos/README.md`:

```markdown
# 14 — Harmonia Popular: Cifras e Acordes Estendidos

**Referências:** Open Music Theory, capítulos sobre harmonia popular/jazz
e cifras (lead sheets) (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Em música popular e jazz, acordes costumam ser escritos como cifras
(lead sheet chord symbols: `Dm7`, `G7`, `Cmaj7`...) em vez de partitura
completa. O `ii7-V7-Imaj7` é o "turnaround" mais comum do jazz — a mesma
lógica funcional dos numerais romanos que você já viu no módulo 06, só
que com acordes de sétima em vez de tríades. Acordes estendidos
(9ª, 11ª, 13ª) empilham mais terças acima da sétima, adicionando cor
harmônica sem mudar a função do acorde: um `ii9` ainda funciona como
`ii`, só soa mais rico.

## O que o script faz

`build_events()` usa `generate_progression` (já existente) com as
figuras de sétima e nona do music21 (`"ii7"`, `"V7"`, `"IMaj7"`, `"ii9"`,
`"V9"`, `"IM9"`) para tocar o turnaround duas vezes: primeiro com
sétimas, depois (após uma pausa) com nonas.

## O que esperar no piano roll

Dois grupos de três blocos de acordes. No primeiro grupo cada acorde tem
4 notas (sétimas); no segundo, cada acorde tem 5 notas (a nona
adicionada) — mesma harmonia, mais denso.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos/licao.py`:

```python
"""Lição 14 - Harmonia Popular: Cifras e Acordes Estendidos."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 14 - Harmonia Popular (Cifras e Acordes Estendidos)"


def build_events() -> list[tuple[int, float, float]]:
    """ii7-V7-IMaj7 (o 'turnaround' de jazz mais comum) seguido, após uma
    pausa, da mesma progressão com acordes estendidos (ii9-V9-IM9) --
    mesma harmonia, mais cor."""
    setimas = generate_progression("C", ["ii7", "V7", "IMaj7"])
    nonas = generate_progression("C", ["ii9", "V9", "IM9"])
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in setimas:
        for pitch_value in chord:
            events.append((pitch_value, start, 1.0))
        start += 1.0
    start += 0.5
    for chord in nonas:
        for pitch_value in chord:
            events.append((pitch_value, start, 1.0))
        start += 1.0
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
        "ii7-V7-IMaj7 (sétimas) seguido de ii9-V9-IM9 (nonas) -- a mesma "
        "progressão funcional, com acordes cada vez mais estendidos."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (módulos 01-14)

Also run the entire suite to confirm Fase 5 is fully green:

Run: `uv run pytest tests/ -v`
Expected: all PASS (211 baseline + 1 new = 212)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/14_harmonia_popular_cifras_e_acordes_estendidos tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 14 - harmonia popular: cifras e acordes estendidos"
```

---

## After this plan

Fase 5 completes módulo 14 with no new `reaper_bridge` code. Módulo 15
(the capstone — multi-instrument composition/arrangement across
bateria/baixo/guitarra/piano/cordas/voz, plus optional live MIDI
keyboard/voice practice) is substantially larger in scope than any prior
módulo and needs its own dedicated design pass (instrument/plugin
guidance, multi-track arrangement structure, how the "parts talk to each
other" content the user specifically asked for) before a plan can be
written — treat it as its own phase, not folded into this one. Módulo 16
(bônus, post-tonal) is the lowest-priority remaining item per the spec.
