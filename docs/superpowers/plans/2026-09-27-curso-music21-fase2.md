# Curso music21 no piano roll — Fase 2 (módulos 06-09: harmonia funcional) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the four "harmonia funcional" lessons (06 Harmonia Funcional/Numerais Romanos, 07 Cadências e Modelo de Frase, 08 Notas de Adorno, 09 Dominantes Secundárias e Modulação) to the music21-in-REAPER-piano-roll course, continuing directly from Fase 1 (already merged to master).

**Architecture:** Unlike Fase 1, this phase needs **no new `reaper_bridge` code** — every lesson reuses `generate_progression` (chords from Roman numerals, already existing and tested) and `write_events_to_track` (variable-duration/simultaneous-note writing, already existing and tested from Fase 1). Each lesson is again a `build_events()` pure function (music21 only) plus a `main()` that connects via `lesson_track()` and writes to a dedicated track — the exact pattern established by Fase 1's modules 01-05.

**Tech Stack:** Python 3.11, music21 10.5.0, reapy, pytest, existing `tests/fakes.py`.

**Spec:** `docs/superpowers/specs/2026-09-27-curso-music21-design.md`

## Global Constraints

- Every `licao.py` separates a pure `build_events()` function (music21 only, no REAPER — unit-testable without REAPER open) from `main()` (the only part doing I/O).
- `licao.py`'s `main()` must catch `ReaperBridgeError` and print a friendly Portuguese message, never let a raw traceback surface.
- Lessons reuse existing `reaper_bridge` functions (`generate_progression`, `write_events_to_track`) instead of duplicating music21/reapy logic — this phase adds zero new `reaper_bridge` code.
- `curso_music21/modulos/NN_xxx` directory names start with digits, so tests import them with `importlib.import_module("curso_music21.modulos.NN_xxx.licao")`, never a `from x.y import z` statement (verified in Fase 1: Python's import machinery accepts non-identifier path segments via `importlib.import_module`; only the `import` statement's parser requires identifiers).
- Each task must APPEND to the existing `tests/test_curso_music21_licoes.py` (created in Fase 1) without disturbing modules 01-05's existing tests in that file.
- music21 User's Guide and Open Music Theory (CC BY-NC-SA, https://viva.pressbooks.pub/openmusictheory/) are cited/linked in READMEs, never copied verbatim.
- Every event/pitch value specified in this plan was verified by directly executing the equivalent code against the real installed music21 10.5.0 / `reaper_bridge.midi.generate_progression` before this plan was written — they are exact, not estimates.

## Review Focus

- Each module's `build_events()` must exactly match this plan's verified literal event list — a transcription slip (wrong pitch, start, or duration) is the single most likely failure mode across all 4 tasks, since each list has 12-24 tuples.
- Módulo 09 passes the numeral string `"V/V"` (a secondary dominant) to `generate_progression` — this syntax isn't exercised by any existing test in the codebase; confirm it's passed through literally, not reformatted or validated against some other list.
- Módulo 08's `build_events()` must produce the two-phrase "esqueleto then preenchida" structure with the 0.5s gap between phrases, not just a flat list of notes — a test that only checks total length would miss a timing bug.
- Track names (`"Curso 06 - ..."` through `"Curso 09 - ..."`) must be distinct from each other and from Fase 1's `"Curso 01" .. "Curso 05"` tracks — a collision would make `lesson_track` clear/overwrite the wrong lesson's track.
- All 4 `build_events()` functions must stay free of any REAPER/reapy import or call — a lesson that accidentally does I/O inside its pure function breaks the "testable without REAPER open" guarantee the whole course relies on.

---

## Task 1: Módulo 06 — Harmonia Funcional (Numerais Romanos)

**Files:**
- Create: `curso_music21/modulos/06_harmonia_funcional_numerais_romanos/__init__.py` (empty)
- Create: `curso_music21/modulos/06_harmonia_funcional_numerais_romanos/README.md`
- Create: `curso_music21/modulos/06_harmonia_funcional_numerais_romanos/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `curso_music21._shared.reaper_track.lesson_track` (existing), `reaper_bridge.midi.generate_progression` and `reaper_bridge.midi.write_events_to_track` (existing), `reaper_bridge.errors.ReaperBridgeError`.
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module, imported by its test via `importlib.import_module("curso_music21.modulos.06_harmonia_funcional_numerais_romanos.licao")`.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/06_harmonia_funcional_numerais_romanos
touch curso_music21/modulos/06_harmonia_funcional_numerais_romanos/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_06 = "curso_music21.modulos.06_harmonia_funcional_numerais_romanos.licao"


def test_modulo_06_build_events_progressao_i_iv_v_i():
    licao = importlib.import_module(MODULO_06)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (65, 1.0, 1.0), (69, 1.0, 1.0), (72, 1.0, 1.0),
        (67, 2.0, 1.0), (71, 2.0, 1.0), (74, 2.0, 1.0),
        (60, 3.0, 1.0), (64, 3.0, 1.0), (67, 3.0, 1.0),
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_06`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/06_harmonia_funcional_numerais_romanos/README.md`:

```markdown
# 06 — Harmonia Funcional (Numerais Romanos)

**Referências:** music21 User's Guide, cap. 23 ("Roman Numeral Analysis") ·
Open Music Theory, capítulo "Roman Numerals"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Numerais romanos descrevem o grau da escala sobre o qual um acorde é
construído, dentro de uma tonalidade: I é o acorde da tônica, IV o da
subdominante, V o da dominante. A progressão I-IV-V-I é o ciclo harmônico
mais básico da música tonal — sai de casa (I), passa por dois pontos de
tensão crescente (IV, V) e volta (I).

## O que o script faz

`build_events()` usa `generate_progression` (já existente em
`reaper_bridge.midi`) para montar os acordes I, IV, V, I em Dó maior, e
toca cada um como um bloco de três notas simultâneas, um atrás do outro.

## O que esperar no piano roll

Quatro blocos de três notas empilhadas, cada bloco com 1 segundo de
duração: Dó-Mi-Sol, depois Fá-Lá-Dó, depois Sol-Si-Ré, e de volta a
Dó-Mi-Sol.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/06_harmonia_funcional_numerais_romanos/licao.py`:

```python
"""Lição 06 - Harmonia Funcional (Numerais Romanos)."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 06 - Harmonia Funcional (Numerais Romanos)"


def build_events() -> list[tuple[int, float, float]]:
    """Progressão I-IV-V-I em Do maior, cada acorde soando simultâneo,
    um atrás do outro -- a base da harmonia funcional tonal."""
    progression = generate_progression("C", ["I", "IV", "V", "I"])
    events: list[tuple[int, float, float]] = []
    for index, chord in enumerate(progression):
        for pitch_value in chord:
            events.append((pitch_value, float(index), 1.0))
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
        "I-IV-V-I em Do maior: tonica, subdominante, dominante, tonica -- "
        "o ciclo harmonico mais basico da tonalidade."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (modules 01-06)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/06_harmonia_funcional_numerais_romanos tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 06 - harmonia funcional (numerais romanos)"
```

---

## Task 2: Módulo 07 — Cadências e Modelo de Frase

**Files:**
- Create: `curso_music21/modulos/07_cadencias_e_modelo_de_frase/__init__.py` (empty)
- Create: `curso_music21/modulos/07_cadencias_e_modelo_de_frase/README.md`
- Create: `curso_music21/modulos/07_cadencias_e_modelo_de_frase/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track`, `generate_progression`, `write_events_to_track`, `ReaperBridgeError` (all existing).
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/07_cadencias_e_modelo_de_frase
touch curso_music21/modulos/07_cadencias_e_modelo_de_frase/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_07 = "curso_music21.modulos.07_cadencias_e_modelo_de_frase.licao"


def test_modulo_07_build_events_quatro_cadencias_com_pausas():
    licao = importlib.import_module(MODULO_07)
    assert licao.build_events() == [
        (67, 0.0, 1.0), (71, 0.0, 1.0), (74, 0.0, 1.0),
        (60, 1.0, 1.0), (64, 1.0, 1.0), (67, 1.0, 1.0),
        (60, 2.5, 1.0), (64, 2.5, 1.0), (67, 2.5, 1.0),
        (67, 3.5, 1.0), (71, 3.5, 1.0), (74, 3.5, 1.0),
        (65, 5.0, 1.0), (69, 5.0, 1.0), (72, 5.0, 1.0),
        (60, 6.0, 1.0), (64, 6.0, 1.0), (67, 6.0, 1.0),
        (67, 7.5, 1.0), (71, 7.5, 1.0), (74, 7.5, 1.0),
        (69, 8.5, 1.0), (72, 8.5, 1.0), (76, 8.5, 1.0),
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_07`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/07_cadencias_e_modelo_de_frase/README.md`:

```markdown
# 07 — Cadências e Modelo de Frase

**Referências:** Open Music Theory, capítulo "Cadences"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma cadência é o ponto de chegada de uma frase musical, e o tipo de
cadência define quanto repouso (ou tensão) ela entrega:

- **Autêntica (V-I)**: o repouso mais completo, a tônica chegando depois
  da dominante.
- **Meia-cadência (I-V)**: termina na dominante, soa "em aberto", pedindo
  continuação.
- **Plagal (IV-I)**: o "amém" dos hinos — menos tensa que a autêntica, mas
  ainda resolve na tônica.
- **Deceptiva (V-vi)**: prepara a resolução na tônica mas desvia para o vi
  grau — uma surpresa.

## O que o script faz

`build_events()` monta as quatro cadências (todas em Dó maior, via
`generate_progression`) e as toca em sequência, com uma pequena pausa
entre cada uma.

## O que esperar no piano roll

Quatro pares de blocos de acordes, com uma lacuna visível entre cada par.
Ouça (ou olhe as notas) e compare o quanto cada par "resolve" de volta
para Dó-Mi-Sol.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/07_cadencias_e_modelo_de_frase/licao.py`:

```python
"""Lição 07 - Cadências e Modelo de Frase."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 07 - Cadencias e Modelo de Frase"

CADENCIAS = [
    ("autentica", ["V", "I"]),
    ("meia_cadencia", ["I", "V"]),
    ("plagal", ["IV", "I"]),
    ("deceptiva", ["V", "vi"]),
]


def build_events() -> list[tuple[int, float, float]]:
    """Quatro cadências de dois acordes em Do maior, tocadas em sequência
    com uma pausa entre elas: autêntica (V-I), meia-cadência (I-V),
    plagal (IV-I) e deceptiva (V-vi) -- para comparar o grau de repouso
    de cada uma."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for _, numerals in CADENCIAS:
        progression = generate_progression("C", numerals)
        for chord in progression:
            for pitch_value in chord:
                events.append((pitch_value, start, 1.0))
            start += 1.0
        start += 0.5
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
        "Quatro cadencias em sequencia, separadas por uma pausa: autentica "
        "(V-I, repouso total), meia-cadencia (I-V, fica em aberto), plagal "
        "(IV-I, o 'amem'), deceptiva (V-vi, surpresa -- nao resolve na tonica)."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (modules 01-07)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/07_cadencias_e_modelo_de_frase tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 07 - cadencias e modelo de frase"
```

---

## Task 3: Módulo 08 — Notas de Adorno

**Files:**
- Create: `curso_music21/modulos/08_notas_de_adorno/__init__.py` (empty)
- Create: `curso_music21/modulos/08_notas_de_adorno/README.md`
- Create: `curso_music21/modulos/08_notas_de_adorno/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track`, `write_events_to_track`, `ReaperBridgeError` (all existing). No `generate_progression`/`generate_scale` needed — pitches are literal (verified below).
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/08_notas_de_adorno
touch curso_music21/modulos/08_notas_de_adorno/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_08 = "curso_music21.modulos.08_notas_de_adorno.licao"


def test_modulo_08_build_events_esqueleto_depois_preenchida():
    licao = importlib.import_module(MODULO_08)
    assert licao.build_events() == [
        (60, 0.0, 0.5), (64, 0.5, 0.5), (67, 1.0, 0.5), (72, 1.5, 0.5),
        (60, 2.5, 0.25), (62, 2.75, 0.25), (64, 3.0, 0.25), (65, 3.25, 0.25),
        (67, 3.5, 0.25), (69, 3.75, 0.25), (71, 4.0, 0.25), (72, 4.25, 0.25),
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_08`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/08_notas_de_adorno/README.md`:

```markdown
# 08 — Notas de Adorno

**Referências:** Open Music Theory, capítulo "Embellishing Tones"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Notas de adorno (non-chord tones) são notas de uma melodia que não
pertencem ao acorde tocado naquele momento — passam rápido, preenchendo o
espaço entre as notas do acorde. A mais comum é a nota de passagem:
preenche o intervalo entre duas notas do acorde andando por grau
conjunto (um passo de escala de cada vez).

## O que o script faz

`build_events()` toca primeiro o "esqueleto" — só as notas do acorde de
Dó (Dó-Mi-Sol-Dó) — e depois a mesma linha preenchida com a escala
completa (Dó-Ré-Mi-Fá-Sol-Lá-Si-Dó), onde Ré, Fá, Lá e Si são notas de
passagem entre as notas do acorde.

## O que esperar no piano roll

Quatro notas espaçadas, uma pausa, e depois oito notas mais rápidas
preenchendo o mesmo contorno melódico (sobe de Dó a Dó).
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/08_notas_de_adorno/licao.py`:

```python
"""Lição 08 - Notas de Adorno."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 08 - Notas de Adorno"

ESQUELETO = [60, 64, 67, 72]
PREENCHIDA = [60, 62, 64, 65, 67, 69, 71, 72]


def build_events() -> list[tuple[int, float, float]]:
    """Toca primeiro só as notas do acorde de Do (esqueleto), depois a
    mesma linha preenchida com notas de passagem (escala completa) --
    mesmo contorno, uma versão decorada com notas de adorno."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for pitch_value in ESQUELETO:
        events.append((pitch_value, start, 0.5))
        start += 0.5
    start += 0.5
    for pitch_value in PREENCHIDA:
        events.append((pitch_value, start, 0.25))
        start += 0.25
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
        "Primeiro so as notas do acorde (Do-Mi-Sol-Do), depois a mesma "
        "linha preenchida com notas de passagem -- mesmo contorno, mais "
        "movimento."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (modules 01-08)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/08_notas_de_adorno tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 08 - notas de adorno"
```

---

## Task 4: Módulo 09 — Dominantes Secundárias e Modulação

**Files:**
- Create: `curso_music21/modulos/09_dominantes_secundarias_e_modulacao/__init__.py` (empty)
- Create: `curso_music21/modulos/09_dominantes_secundarias_e_modulacao/README.md`
- Create: `curso_music21/modulos/09_dominantes_secundarias_e_modulacao/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track`, `generate_progression`, `write_events_to_track`, `ReaperBridgeError` (all existing).
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/09_dominantes_secundarias_e_modulacao
touch curso_music21/modulos/09_dominantes_secundarias_e_modulacao/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_09 = "curso_music21.modulos.09_dominantes_secundarias_e_modulacao.licao"


def test_modulo_09_build_events_i_v_de_v_v_i():
    licao = importlib.import_module(MODULO_09)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (74, 1.0, 1.0), (78, 1.0, 1.0), (81, 1.0, 1.0),
        (67, 2.0, 1.0), (71, 2.0, 1.0), (74, 2.0, 1.0),
        (60, 3.0, 1.0), (64, 3.0, 1.0), (67, 3.0, 1.0),
    ]
```

This pins `generate_progression("C", ["I", "V/V", "V", "I"])` producing
`[[60,64,67], [74,78,81], [67,71,74], [60,64,67]]` — `V/V` in Dó maior is
Ré maior (D-F#-A = 74,78,81), verified live against music21 before this
plan was written.

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_09`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/09_dominantes_secundarias_e_modulacao/README.md`:

```markdown
# 09 — Dominantes Secundárias e Modulação

**Referências:** Open Music Theory, capítulo "Secondary Dominants /
Tonicization" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma dominante secundária "empresta" a dominante de outro grau da escala
por um instante, tonicizando-o — fazendo aquele acorde soar
momentaneamente como se fosse a tônica de outra tonalidade, sem
realmente modular. `V/V` é a dominante do V: em Dó maior, o V é Sol, e a
dominante de Sol é Ré maior. Tocar V/V antes do V de verdade reforça a
chegada na dominante.

## O que o script faz

`build_events()` usa `generate_progression` com a notação `"V/V"` (que o
music21 entende nativamente) para montar I - V/V - V - I em Dó maior.

## O que esperar no piano roll

Quatro blocos de acordes: Dó-Mi-Sol, depois Ré-Fá#-Lá (o V/V — repare no
Fá sustenido, fora da tonalidade de Dó!), depois Sol-Si-Ré, e de volta a
Dó-Mi-Sol.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/09_dominantes_secundarias_e_modulacao/licao.py`:

```python
"""Lição 09 - Dominantes Secundárias e Modulação."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 09 - Dominantes Secundarias e Modulacao"


def build_events() -> list[tuple[int, float, float]]:
    """I - V/V - V - I em Do maior: o V/V (dominante da dominante)
    tonaciza o V por um instante antes de resolver -- um gostinho de
    modulação sem sair de fato da tonalidade."""
    progression = generate_progression("C", ["I", "V/V", "V", "I"])
    events: list[tuple[int, float, float]] = []
    for index, chord in enumerate(progression):
        for pitch_value in chord:
            events.append((pitch_value, float(index), 1.0))
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
        "I - V/V - V - I: o segundo acorde 'pisca' na tonalidade de Sol "
        "(a dominante de Sol) antes de resolver no V de verdade."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (modules 01-09)

Also run the entire suite to confirm Fase 2 is fully green:

Run: `uv run pytest tests/ -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/09_dominantes_secundarias_e_modulacao tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 09 - dominantes secundarias e modulacao"
```

---

## After this plan

Fase 2 delivers modules 06-09, all reusing existing `reaper_bridge`
functions with no new library code. Módulos 10-12 (condução de vozes,
contraponto, forma musical) get their own plan next, per the spec's
"Ordem de entrega" section — note that módulo 10 (condução de vozes) may
need new `reaper_bridge` support for detecting parallel fifths/octaves,
flagged as an open implementation question in the spec itself.
