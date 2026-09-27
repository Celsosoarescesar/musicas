# Curso music21 no piano roll — Fase 3 (módulos 10-12: condução de vozes, contraponto, forma) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add módulos 10 (Condução de Vozes), 11 (Contraponto) and 12 (Forma Musical) to the music21-in-REAPER-piano-roll course, continuing directly from Fases 1-2 (already merged to master).

**Architecture:** Like Fase 2, this phase needs **no new `reaper_bridge` code**. Módulos 10 and 11 introduce two-voice lessons: each writes to **two separate REAPER tracks** (one per voice) using two `lesson_track()`/`write_events_to_track()` calls in `main()`, instead of the single-track pattern used by every módulo so far. Both also use `music21.voiceLeading.VoiceLeadingQuartet` — confirmed live against the installed music21 10.5.0 to correctly detect parallel fifths/octaves/unisons — to *actually compute* whether a given pair of voices is valid, rather than asserting it in prose. This resolves the spec's open question about módulo 10 needing new `reaper_bridge` support for parallel-motion detection: music21 already has it, no new library code needed. Módulo 12 is single-track and reuses `generate_progression`, exactly like módulos 06/07/09.

**Tech Stack:** Python 3.11, music21 10.5.0 (`music21.voiceLeading.VoiceLeadingQuartet` used directly for the first time in this course), reapy, pytest, `tests/fakes.py`.

**Spec:** `docs/superpowers/specs/2026-09-27-curso-music21-design.md`

## Global Constraints

- Every `licao.py` separates pure `build_*()` functions (music21 only, no REAPER — unit-testable without REAPER open) from `main()` (the only part doing I/O). Módulos 10 and 11 have *multiple* `build_events_*()` functions (one per voice) plus one pure analysis function (`build_deteccao_paralelas()` / `build_verificacao()`) — all still free of any `reaper_bridge`/reapy call.
- `licao.py`'s `main()` must catch `ReaperBridgeError` and print a friendly Portuguese message, never let a raw traceback surface. Módulos 10 and 11's `main()` makes two `lesson_track()` + `write_events_to_track()` call pairs (one per voice) inside the same `try` block.
- Lessons reuse existing `reaper_bridge` functions (`generate_progression`, `write_events_to_track`) instead of duplicating music21/reapy logic — this phase adds zero new `reaper_bridge` code. New in this phase: direct use of `music21.voiceLeading.VoiceLeadingQuartet` inside lesson scripts (not wrapped by `reaper_bridge` — it's pure music21 analysis, consistent with how módulo 04 already imports `music21.interval` directly).
- `curso_music21/modulos/NN_xxx` directory names start with digits, so tests import them with `importlib.import_module("curso_music21.modulos.NN_xxx.licao")`, never a `from x.y import z` statement.
- Each task must APPEND to the existing `tests/test_curso_music21_licoes.py` (created in Fase 1, now holding módulos 01-09) without disturbing the existing tests in that file.
- Track names must be distinct across all 12 módulos built so far (01 through 12; módulos 10 and 11 each register *two* track names). No collisions.
- music21 User's Guide and Open Music Theory (CC BY-NC-SA, https://viva.pressbooks.pub/openmusictheory/) are cited/linked in READMEs, never copied verbatim.
- Every event/pitch value and every `VoiceLeadingQuartet` verdict specified in this plan was verified by directly executing the equivalent code against the real installed music21 10.5.0 before this plan was written — they are exact, not estimates.

## Review Focus

- `build_deteccao_paralelas()` (módulo 10) and `build_verificacao()` (módulo 11) must call the real `music21.voiceLeading.VoiceLeadingQuartet`/`.parallelFifth()`/`.parallelOctave()`/`.parallelUnison()` methods and return their actual result — not a hardcoded `True`/`False` that happens to match the expected test value. A lazy implementation faking this would pass a naive test but defeat the lesson's whole point (live detection).
- Módulos 10 and 11 each write to **two** REAPER tracks in one `main()` — confirm both `lesson_track()` calls use the correct, distinct track name and each `write_events_to_track()` call is paired with the matching voice's events (a copy-paste slip could easily write the wrong voice to the wrong track).
- Each module's literal expected lists (event tuples for 10/11/12, the boolean tuple for 10, the boolean for 11) must exactly match this plan's pre-verified values — the counterpoint line (módulo 11) has 7 notes per voice, the single largest literal list transcribed in this phase.
- Track names across all 14 registered track strings (12 módulos, 2 each for módulos 10 and 11) must be pairwise distinct — a collision would make `lesson_track` clear/overwrite the wrong voice's or wrong module's track.
- All `build_*()` functions (including the two analysis functions) must stay free of any REAPER/reapy import or call — `music21.voiceLeading`/`music21.note` are music21-only and safe to use inside pure functions; `lesson_track`/`write_events_to_track` must only ever appear inside `main()`.

---

## Task 1: Módulo 10 — Condução de Vozes

**Files:**
- Create: `curso_music21/modulos/10_conducao_de_vozes/__init__.py` (empty)
- Create: `curso_music21/modulos/10_conducao_de_vozes/README.md`
- Create: `curso_music21/modulos/10_conducao_de_vozes/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `curso_music21._shared.reaper_track.lesson_track` (existing), `reaper_bridge.midi.write_events_to_track` (existing), `reaper_bridge.errors.ReaperBridgeError`, `music21.note.Note`, `music21.voiceLeading.VoiceLeadingQuartet` (new usage in this course, but not new library code).
- Produces: `build_events_superior() -> list[tuple[int, float, float]]`, `build_events_inferior() -> list[tuple[int, float, float]]`, `build_deteccao_paralelas() -> tuple[bool, bool]` in this module, imported by tests via `importlib.import_module("curso_music21.modulos.10_conducao_de_vozes.licao")`.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/10_conducao_de_vozes
touch curso_music21/modulos/10_conducao_de_vozes/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_10 = "curso_music21.modulos.10_conducao_de_vozes.licao"


def test_modulo_10_build_events_superior_duas_frases_com_pausa():
    licao = importlib.import_module(MODULO_10)
    assert licao.build_events_superior() == [
        (67, 0.0, 1.0), (69, 1.0, 1.0), (67, 2.5, 1.0), (65, 3.5, 1.0),
    ]


def test_modulo_10_build_events_inferior_duas_frases_com_pausa():
    licao = importlib.import_module(MODULO_10)
    assert licao.build_events_inferior() == [
        (60, 0.0, 1.0), (62, 1.0, 1.0), (60, 2.5, 1.0), (62, 3.5, 1.0),
    ]


def test_modulo_10_build_deteccao_paralelas_confirma_problema_e_correcao():
    licao = importlib.import_module(MODULO_10)
    assert licao.build_deteccao_paralelas() == (True, False)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_10`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/10_conducao_de_vozes/README.md`:

```markdown
# 10 — Condução de Vozes

**Referências:** Open Music Theory, capítulo "Voice Leading"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Na condução de vozes tradicional, duas vozes não devem se mover em
quintas ou oitavas paralelas — manter a mesma distância "perfeita" entre
elas de um acorde para o outro enfraquece a independência das vozes.
Movimento contrário (as vozes andam em direções opostas) é a forma mais
segura de evitar isso.

## O que o script faz

Duas vozes, em faixas separadas. Cada uma toca duas frases curtas: a
primeira anda em movimento paralelo (quinta paralela entre as vozes), a
segunda faz a mesma ideia mas com movimento contrário. O script usa
`music21.voiceLeading.VoiceLeadingQuartet` para *detectar de verdade* se
há quinta paralela em cada versão, e imprime o resultado.

## O que esperar no piano roll

Duas faixas, quatro notas cada. Compare a "Voz Superior" nas duas
metades: na primeira ela sobe junto com a "Voz Inferior" (mantendo a
mesma distância vertical), na segunda ela desce enquanto a inferior sobe.
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/10_conducao_de_vozes/licao.py`:

```python
"""Lição 10 - Condução de Vozes."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import note, voiceLeading  # noqa: E402

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402

TRACK_NAME_SUPERIOR = "Curso 10 - Conducao de Vozes (Voz Superior)"
TRACK_NAME_INFERIOR = "Curso 10 - Conducao de Vozes (Voz Inferior)"

SUPERIOR_PROBLEMATICA = [67, 69]  # Sol4 -> La4
INFERIOR_PROBLEMATICA = [60, 62]  # Do4 -> Re4
SUPERIOR_CORRIGIDA = [67, 65]  # Sol4 -> Fa4
INFERIOR_CORRIGIDA = [60, 62]  # Do4 -> Re4


def _duas_frases_com_pausa(
    problematica: list[int], corrigida: list[int]
) -> list[tuple[int, float, float]]:
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for pitch_value in problematica:
        events.append((pitch_value, start, 1.0))
        start += 1.0
    start += 0.5
    for pitch_value in corrigida:
        events.append((pitch_value, start, 1.0))
        start += 1.0
    return events


def build_events_superior() -> list[tuple[int, float, float]]:
    """Voz superior: primeiro a versão com quinta paralela (Sol4-La4),
    depois (após uma pausa) a versão corrigida com movimento contrário
    (Sol4-Fa4)."""
    return _duas_frases_com_pausa(SUPERIOR_PROBLEMATICA, SUPERIOR_CORRIGIDA)


def build_events_inferior() -> list[tuple[int, float, float]]:
    """Voz inferior: Do4-Re4 nas duas versões -- só a voz superior muda."""
    return _duas_frases_com_pausa(INFERIOR_PROBLEMATICA, INFERIOR_CORRIGIDA)


def build_deteccao_paralelas() -> tuple[bool, bool]:
    """Usa music21.voiceLeading.VoiceLeadingQuartet para detectar de
    verdade se há quinta paralela entre as duas vozes em cada versão --
    retorna (problemática_tem_quinta_paralela, corrigida_tem_quinta_paralela)."""
    problematica = voiceLeading.VoiceLeadingQuartet(
        note.Note(midi=SUPERIOR_PROBLEMATICA[0]),
        note.Note(midi=SUPERIOR_PROBLEMATICA[1]),
        note.Note(midi=INFERIOR_PROBLEMATICA[0]),
        note.Note(midi=INFERIOR_PROBLEMATICA[1]),
    )
    corrigida = voiceLeading.VoiceLeadingQuartet(
        note.Note(midi=SUPERIOR_CORRIGIDA[0]),
        note.Note(midi=SUPERIOR_CORRIGIDA[1]),
        note.Note(midi=INFERIOR_CORRIGIDA[0]),
        note.Note(midi=INFERIOR_CORRIGIDA[1]),
    )
    return problematica.parallelFifth(), corrigida.parallelFifth()


def main() -> None:
    superior_events = build_events_superior()
    inferior_events = build_events_inferior()
    problematica_tem_paralela, corrigida_tem_paralela = build_deteccao_paralelas()
    try:
        project, _track = lesson_track(TRACK_NAME_SUPERIOR)
        write_events_to_track(project, TRACK_NAME_SUPERIOR, superior_events)
        project, _track = lesson_track(TRACK_NAME_INFERIOR)
        write_events_to_track(project, TRACK_NAME_INFERIOR, inferior_events)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(
        f"Confira as faixas '{TRACK_NAME_SUPERIOR}' e "
        f"'{TRACK_NAME_INFERIOR}' no piano roll do REAPER."
    )
    print(
        f"Versão problemática tem quinta paralela: {problematica_tem_paralela}. "
        f"Versão corrigida tem quinta paralela: {corrigida_tem_paralela}."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (módulos 01-10)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/10_conducao_de_vozes tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 10 - conducao de vozes"
```

---

## Task 2: Módulo 11 — Contraponto

**Files:**
- Create: `curso_music21/modulos/11_contraponto/__init__.py` (empty)
- Create: `curso_music21/modulos/11_contraponto/README.md`
- Create: `curso_music21/modulos/11_contraponto/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track`, `write_events_to_track`, `ReaperBridgeError` (all existing), `music21.note.Note`, `music21.voiceLeading.VoiceLeadingQuartet`.
- Produces: `build_events_cantus_firmus() -> list[tuple[int, float, float]]`, `build_events_contraponto() -> list[tuple[int, float, float]]`, `build_verificacao() -> bool` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/11_contraponto
touch curso_music21/modulos/11_contraponto/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_11 = "curso_music21.modulos.11_contraponto.licao"


def test_modulo_11_build_events_cantus_firmus():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_events_cantus_firmus() == [
        (60, 0.0, 1.0), (62, 1.0, 1.0), (64, 2.0, 1.0), (65, 3.0, 1.0),
        (64, 4.0, 1.0), (62, 5.0, 1.0), (60, 6.0, 1.0),
    ]


def test_modulo_11_build_events_contraponto():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_events_contraponto() == [
        (72, 0.0, 1.0), (69, 1.0, 1.0), (67, 2.0, 1.0), (69, 3.0, 1.0),
        (72, 4.0, 1.0), (69, 5.0, 1.0), (72, 6.0, 1.0),
    ]


def test_modulo_11_build_verificacao_confirma_contraponto_valido():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_verificacao() is True
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_11`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/11_contraponto/README.md`:

```markdown
# 11 — Contraponto

**Referências:** Open Music Theory, capítulo "Species Counterpoint"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Contraponto de primeira espécie: uma nota de contraponto para cada nota
do cantus firmus (a melodia fixa), sempre em intervalos consonantes
(uníssono, 3ª, 5ª, 6ª, 8ª), evitando quintas e oitavas paralelas entre as
duas vozes — a mesma regra do módulo 10, aplicada nota a nota numa
melodia inteira. É a técnica que Bach (e os compositores antes dele)
usavam para escrever vozes independentes que soam bem juntas — o que
volta a aparecer no módulo 13, analisando corais de Bach de verdade.

## O que o script faz

Toca o cantus firmus (Dó-Ré-Mi-Fá-Mi-Ré-Dó) numa faixa e o contraponto
escrito sobre ele em outra. `build_verificacao()` confirma, nota por
nota, que todos os intervalos são consonantes e que não há quinta,
oitava ou uníssono paralelo entre nenhum par de notas consecutivas —
usando o mesmo `music21.voiceLeading.VoiceLeadingQuartet` do módulo 10.

## O que esperar no piano roll

Duas faixas com sete notas cada, tocando juntas. A primeira e a última
nota das duas vozes formam uma oitava (começo e fim tradicionais do
contraponto de primeira espécie).
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/11_contraponto/licao.py`:

```python
"""Lição 11 - Contraponto."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import note, voiceLeading  # noqa: E402

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402

TRACK_NAME_CANTUS_FIRMUS = "Curso 11 - Contraponto (Cantus Firmus)"
TRACK_NAME_CONTRAPONTO = "Curso 11 - Contraponto (Contraponto)"

CANTUS_FIRMUS = [60, 62, 64, 65, 64, 62, 60]  # Do Re Mi Fa Mi Re Do
CONTRAPONTO = [72, 69, 67, 69, 72, 69, 72]
CONSONANCIAS = {0, 3, 4, 7, 8, 9, 12}  # unissono, 3m, 3M, 5J, 6m, 6M, 8J


def _melodia_em_eventos(pitches: list[int]) -> list[tuple[int, float, float]]:
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for pitch_value in pitches:
        events.append((pitch_value, start, 1.0))
        start += 1.0
    return events


def build_events_cantus_firmus() -> list[tuple[int, float, float]]:
    """A melodia fixa (cantus firmus), nota contra nota."""
    return _melodia_em_eventos(CANTUS_FIRMUS)


def build_events_contraponto() -> list[tuple[int, float, float]]:
    """A linha de contraponto de primeira espécie, escrita sobre o
    cantus firmus."""
    return _melodia_em_eventos(CONTRAPONTO)


def build_verificacao() -> bool:
    """Confirma que o contraponto segue as regras do primeiro espécie:
    só consonâncias, sem quintas/oitavas/unissonos paralelos entre as
    vozes, usando music21.voiceLeading.VoiceLeadingQuartet para checar
    de verdade cada par de notas consecutivas."""
    for baixo, cima in zip(CANTUS_FIRMUS, CONTRAPONTO):
        if (cima - baixo) not in CONSONANCIAS:
            return False
    for index in range(len(CANTUS_FIRMUS) - 1):
        vlq = voiceLeading.VoiceLeadingQuartet(
            note.Note(midi=CONTRAPONTO[index]),
            note.Note(midi=CONTRAPONTO[index + 1]),
            note.Note(midi=CANTUS_FIRMUS[index]),
            note.Note(midi=CANTUS_FIRMUS[index + 1]),
        )
        if vlq.parallelFifth() or vlq.parallelOctave() or vlq.parallelUnison():
            return False
    return True


def main() -> None:
    cantus_events = build_events_cantus_firmus()
    contraponto_events = build_events_contraponto()
    valido = build_verificacao()
    try:
        project, _track = lesson_track(TRACK_NAME_CANTUS_FIRMUS)
        write_events_to_track(project, TRACK_NAME_CANTUS_FIRMUS, cantus_events)
        project, _track = lesson_track(TRACK_NAME_CONTRAPONTO)
        write_events_to_track(project, TRACK_NAME_CONTRAPONTO, contraponto_events)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(
        f"Confira as faixas '{TRACK_NAME_CANTUS_FIRMUS}' e "
        f"'{TRACK_NAME_CONTRAPONTO}' no piano roll do REAPER."
    )
    print(f"Contraponto válido (só consonâncias, sem paralelas proibidas): {valido}.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (módulos 01-11)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/11_contraponto tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 11 - contraponto"
```

---

## Task 3: Módulo 12 — Forma Musical

**Files:**
- Create: `curso_music21/modulos/12_forma_musical/__init__.py` (empty)
- Create: `curso_music21/modulos/12_forma_musical/README.md`
- Create: `curso_music21/modulos/12_forma_musical/licao.py`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `lesson_track`, `generate_progression`, `write_events_to_track`, `ReaperBridgeError` (all existing).
- Produces: `build_events() -> list[tuple[int, float, float]]` in this module.

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/12_forma_musical
touch curso_music21/modulos/12_forma_musical/__init__.py
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_12 = "curso_music21.modulos.12_forma_musical.licao"


def test_modulo_12_build_events_periodo_antecedente_e_consequente():
    licao = importlib.import_module(MODULO_12)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (65, 1.0, 1.0), (69, 1.0, 1.0), (72, 1.0, 1.0),
        (67, 2.0, 1.0), (71, 2.0, 1.0), (74, 2.0, 1.0),
        (60, 3.5, 1.0), (64, 3.5, 1.0), (67, 3.5, 1.0),
        (65, 4.5, 1.0), (69, 4.5, 1.0), (72, 4.5, 1.0),
        (67, 5.5, 1.0), (71, 5.5, 1.0), (74, 5.5, 1.0),
        (60, 6.5, 1.0), (64, 6.5, 1.0), (67, 6.5, 1.0),
    ]
```

This pins `generate_progression("C", ["I","IV","V"])` (antecedente) followed
by `generate_progression("C", ["I","IV","V","I"])` (consequente, identical
to módulo 06's exact progression), separated by a 0.5s gap — verified live
against music21 before this plan was written.

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_12`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write the README**

Create `curso_music21/modulos/12_forma_musical/README.md`:

```markdown
# 12 — Forma Musical

**Referências:** Open Music Theory, capítulo "Form: Phrase, Period,
Sentence" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Um período é a unidade de forma mais básica: duas frases relacionadas,
geralmente com material parecido no início, onde a primeira (frase
antecedente) termina numa cadência aberta e a segunda (frase
consequente) termina numa cadência fechada — como uma pergunta seguida
de uma resposta.

## O que o script faz

`build_events()` monta uma frase antecedente (I-IV-V em Dó maior,
terminando em meia-cadência) e, após uma pausa, a frase consequente
(I-IV-V-I, terminando em cadência autêntica) — reaproveitando
`generate_progression`, já usado nos módulos 06, 07 e 09.

## O que esperar no piano roll

Dois grupos de blocos de acordes separados por uma pausa: o primeiro
grupo (3 acordes) termina em Sol-Si-Ré (dominante, em aberto); o segundo
grupo (4 acordes) começa igual mas termina de volta em Dó-Mi-Sol
(tônica, resolvido).
```

- [ ] **Step 5: Write `licao.py`**

Create `curso_music21/modulos/12_forma_musical/licao.py`:

```python
"""Lição 12 - Forma Musical."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 12 - Forma Musical"


def build_events() -> list[tuple[int, float, float]]:
    """Um período clássico: frase antecedente (I-IV-V, termina em meia
    cadência -- a 'pergunta') seguida, após uma pausa, da frase
    consequente (I-IV-V-I, termina em cadência autêntica -- a
    'resposta'). As duas frases compartilham a mesma abertura e só se
    diferenciam no final."""
    antecedente = generate_progression("C", ["I", "IV", "V"])
    consequente = generate_progression("C", ["I", "IV", "V", "I"])
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in antecedente:
        for pitch_value in chord:
            events.append((pitch_value, start, 1.0))
        start += 1.0
    start += 0.5
    for chord in consequente:
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
        "Frase antecedente (I-IV-V, 'pergunta', termina em aberto) seguida "
        "da frase consequente (I-IV-V-I, 'resposta', termina resolvida) -- "
        "um período clássico."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (módulos 01-12)

Also run the entire suite to confirm Fase 3 is fully green:

Run: `uv run pytest tests/ -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/12_forma_musical tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 12 - forma musical"
```

---

## After this plan

Fase 3 delivers módulos 10-12, all reusing existing `reaper_bridge`
functions plus direct (already-verified) use of `music21.voiceLeading`.
Módulo 13 (Música Real: Corpus e Análise) gets its own plan next, per the
spec's "Ordem de entrega" section — this is the first módulo that will
actually call `write_score_to_tracks` (built in Fase 1 but unused since),
so its plan must first fix the two parked issues flagged during Fase 1's
final review: `write_score_to_tracks` isn't idempotent when reusing an
existing track, and two same-named parts in one `Score` collapse onto one
track (real risk for Bach chorales' SATB voices, which can share names
across different corpus files).
