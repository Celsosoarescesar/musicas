# Curso music21 no piano roll — Fase 6 (módulo 15: capstone — composição e arranjo multi-instrumental) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add módulo 15 — the course's capstone — to the music21-in-REAPER-piano-roll course. It composes a short original piece (a motif developed through transposition, inversion, and retrograde, over the I-IV-V-I progression already used in módulos 06/12) and arranges it across 6 REAPER tracks (Voz, Piano, Baixo, Bateria, Guitarra, Cordas), each with a deliberately distinct rhythmic/textural role.

**Architecture:** No new `reaper_bridge` code. `main()` makes 6 `lesson_track()` + `write_events_to_track()` pairs (one per instrument) inside a single `try`/`except ReaperBridgeError`, extending the two-track pattern from módulos 10/11 to six. It does **not** call `reaper_add_fx` — per an explicit design decision, instrument/plugin assignment is left to the user via README instructions, since a hardcoded plugin name would fail on machines without that exact plugin installed. The melody (Voz) is built from a 4-note motif expressed in **scale degrees** (not semitones) and transformed via transposition/inversion/retrograde — a small diatonic helper (`grau_para_midi`) converts scale degrees to MIDI, guaranteeing every transformation stays in key automatically (verified live before this plan was written).

**Tech Stack:** Python 3.11, reapy, pytest, `tests/fakes.py`. No music21 calls needed in this module — the harmony is a fixed, already-verified pitch list (reused from módulo 06), and the motif transformations are pure integer arithmetic.

**Spec:** `docs/superpowers/specs/2026-09-27-curso-music21-design.md` (overall curriculum) and `docs/superpowers/specs/2026-09-27-curso-music21-modulo15-design.md` (this módulo's detailed design — read this one first, it has the full musical rationale and verified data tables).

## Global Constraints

- Every `build_events_*()` function is pure (no REAPER/reapy call) — six of them this phase, one per instrument.
- `main()` must catch `ReaperBridgeError` and print a friendly Portuguese message, never let a raw traceback surface. It wraps all 6 track-writing calls in a single `try` block.
- `main()` must **not** call `reaper_add_fx` or any plugin-assignment function — this was an explicit design decision (confirmed with the user): instrument assignment is a README instruction, not code, so the lesson never fails on a machine missing a specific plugin.
- `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental` starts with a digit, so tests import it with `importlib.import_module("curso_music21.modulos.15_composicao_e_arranjo_multi_instrumental.licao")`.
- Task 2 must APPEND to `licao.py` (adding imports, functions, and `main()`) without disturbing Task 1's `grau_para_midi`, `build_events_voz`, `build_events_piano`, `build_events_baixo` — and must APPEND to the existing `tests/test_curso_music21_licoes.py` (holds módulos 01-14) without disturbing its existing tests.
- Track names (`"Curso 15 - Composição e Arranjo (Voz)"` through `"...(Cordas)"`, six total) must be distinct from every track name registered by módulos 01-14 and from each other.
- The README (written in Task 2) must include two sections no prior módulo's README had: **"Como as partes conversam"** (explicitly discussing why each instrument has a different rhythmic/textural role) and **"Prática com voz e teclado MIDI (opcional)"** (prose-only instructions to record a live take using REAPER's own UI — no new code).
- Every event list, the motif-transformation table, and the diatonic-conversion arithmetic in this plan were verified by direct execution before this plan was written — exact, not estimated. See the módulo 15 design spec for the full verification narrative.

## Review Focus

- `grau_para_midi`'s handling of negative `grau` values (used by `INVERSAO = [0, -1, -2, 0]`) must match the pre-verified table exactly — Python's `divmod` with negative numbers is a common source of off-by-one bugs, and this is the first diatonic-arithmetic helper in the course.
- `build_events_voz`'s four cells must land on the correct chord in sequence (motif→I, transposição→IV, inversão→V, retrógrado→I) — a swapped order would still produce "valid-looking" notes but break the intended motif-development narrative and the retrógrado's satisfying return to the tonic.
- `main()`'s single `try` block must wrap all 6 track-writing calls (not, say, only the first one, leaving the rest unprotected), and must contain zero calls to `reaper_add_fx` anywhere — confirmed design decision, not an oversight to "fix."
- All 15 registered track names across módulos 01-15 remain pairwise distinct (the 6 new ones registered this phase, checked against each other and against 01-14).
- Task 2's edit to `licao.py`'s import section must not silently break Task 1's already-tested functions (e.g., inserting new imports in a way that shadows a name, or reordering constants such that `PROGRESSAO` is referenced before definition).

---

## Task 1: Núcleo harmônico/melódico — motivo, transformações, voz/piano/baixo

**Files:**
- Create: `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/__init__.py` (empty)
- Create: `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/licao.py` (partial — Task 2 extends it)
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: nothing outside this file (no `reaper_bridge`/`curso_music21._shared` imports needed yet — these three functions are pure arithmetic).
- Produces: `grau_para_midi(grau: int, tonica: int = 60) -> int`, `build_events_voz() -> list[tuple[int, float, float]]`, `build_events_piano() -> list[tuple[int, float, float]]`, `build_events_baixo() -> list[tuple[int, float, float]]`, plus the module-level constants `PROGRESSAO`, `INTERVALOS_MAIOR`, `MOTIVO`, `TRANSPOSICAO`, `INVERSAO`, `RETROGRADO`, `CELULAS_MELODICAS` — all consumed by Task 2 (which adds the remaining 3 instruments and `main()` to the same file, reusing `PROGRESSAO`).

- [ ] **Step 1: Create the package file**

```bash
mkdir -p curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental
touch curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_curso_music21_licoes.py`:

```python
MODULO_15 = "curso_music21.modulos.15_composicao_e_arranjo_multi_instrumental.licao"


def test_modulo_15_build_events_voz_motivo_e_transformacoes():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_voz() == [
        (60, 0.0, 0.5), (62, 0.5, 0.5), (64, 1.0, 0.5), (60, 1.5, 0.5),
        (65, 2.0, 0.5), (67, 2.5, 0.5), (69, 3.0, 0.5), (65, 3.5, 0.5),
        (60, 4.0, 0.5), (59, 4.5, 0.5), (57, 5.0, 0.5), (60, 5.5, 0.5),
        (60, 6.0, 0.5), (64, 6.5, 0.5), (62, 7.0, 0.5), (60, 7.5, 0.5),
    ]


def test_modulo_15_build_events_piano_acordes_em_bloco():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_piano() == [
        (60, 0.0, 2.0), (64, 0.0, 2.0), (67, 0.0, 2.0),
        (65, 2.0, 2.0), (69, 2.0, 2.0), (72, 2.0, 2.0),
        (67, 4.0, 2.0), (71, 4.0, 2.0), (74, 4.0, 2.0),
        (60, 6.0, 2.0), (64, 6.0, 2.0), (67, 6.0, 2.0),
    ]


def test_modulo_15_build_events_baixo_fundamental_sustentada():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_baixo() == [
        (48, 0.0, 2.0), (53, 2.0, 2.0), (55, 4.0, 2.0), (48, 6.0, 2.0),
    ]
```

This pins the motif-transformation arithmetic exactly (verified live: a
4-note diatonic motif `[0,1,2,0]` — Dó-Ré-Mi-Dó — transposed up 3 scale
degrees lands exactly on the IV chord's root, inverted around the tonic
for the V chord, and reversed for the final return to I), plus the
I-IV-V-I progression (`[[60,64,67],[65,69,72],[67,71,74],[60,64,67]]`,
identical to módulo 06's) driving both `build_events_piano` (block
chords, 2.0s each) and `build_events_baixo` (root an octave down,
sustained 2.0s each).

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_15`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 4: Write `licao.py` (partial — Task 2 extends this same file)**

Create `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/licao.py`:

```python
"""Lição 15 - Composição e Arranjo Multi-Instrumental (capstone)."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

PROGRESSAO = [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]]  # I-IV-V-I

INTERVALOS_MAIOR = [0, 2, 4, 5, 7, 9, 11]


def grau_para_midi(grau: int, tonica: int = 60) -> int:
    """Converte um grau de escala (relativo à tônica) em MIDI, usando os
    intervalos da escala maior -- garante que qualquer transformação do
    motivo continue dentro do tom, sem precisar checar nota por nota."""
    oitava, posicao = divmod(grau, 7)
    return tonica + oitava * 12 + INTERVALOS_MAIOR[posicao]


MOTIVO = [0, 1, 2, 0]  # Do-Re-Mi-Do, em graus de escala
TRANSPOSICAO = [grau + 3 for grau in MOTIVO]  # sobe uma 4a diatonica -> cai no IV
INVERSAO = [-grau for grau in MOTIVO]  # inverte em torno da tonica
RETROGRADO = list(reversed(MOTIVO))

CELULAS_MELODICAS = [MOTIVO, TRANSPOSICAO, INVERSAO, RETROGRADO]


def build_events_voz() -> list[tuple[int, float, float]]:
    """A melodia principal: o motivo original (sobre o I), transposto
    (sobre o IV), invertido (sobre o V) e em retrógrado (sobre o I final)
    -- as quatro transformações clássicas de motivo, uma sobre cada
    acorde da progressão I-IV-V-I."""
    events: list[tuple[int, float, float]] = []
    chord_start = 0.0
    for celula in CELULAS_MELODICAS:
        note_start = chord_start
        for grau in celula:
            events.append((grau_para_midi(grau), note_start, 0.5))
            note_start += 0.5
        chord_start += 2.0
    return events


def build_events_piano() -> list[tuple[int, float, float]]:
    """Acompanhamento harmônico (comping): os acordes da progressão
    I-IV-V-I em bloco, um a cada 2 segundos."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in PROGRESSAO:
        for pitch_value in chord:
            events.append((pitch_value, start, 2.0))
        start += 2.0
    return events


def build_events_baixo() -> list[tuple[int, float, float]]:
    """A fundação harmônica: só a fundamental de cada acorde, uma oitava
    abaixo, sustentada pelos 2 segundos inteiros -- a bateria (adicionada
    na próxima tarefa) trava o groove com essas trocas de nota."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in PROGRESSAO:
        events.append((chord[0] - 12, start, 2.0))
        start += 2.0
    return events
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_15`
Expected: all 3 PASS

- [ ] **Step 6: Commit**

```bash
git add curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 15 core (motivo, transformacoes, voz/piano/baixo)"
```

---

## Task 2: Camada rítmica/textural + integração — bateria, guitarra, cordas, main(), README

**Files:**
- Modify: `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/licao.py` (add imports, 3 more `build_events_*`, 6 `TRACK_NAME_*` constants, `main()`)
- Create: `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/README.md`
- Modify: `tests/test_curso_music21_licoes.py`

**Interfaces:**
- Consumes: `curso_music21._shared.reaper_track.lesson_track` (existing), `reaper_bridge.midi.write_events_to_track` (existing), `reaper_bridge.errors.ReaperBridgeError`, and Task 1's `PROGRESSAO` constant (reused, not redefined).
- Produces: `build_events_bateria() -> list[tuple[int, float, float]]`, `build_events_guitarra() -> list[tuple[int, float, float]]`, `build_events_cordas() -> list[tuple[int, float, float]]`, `main() -> None` in the same module.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_curso_music21_licoes.py`:

```python
def test_modulo_15_build_events_bateria_kick_alinhado_com_baixo():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_bateria() == [
        (36, 0.0, 0.5), (42, 0.5, 0.5), (38, 1.0, 0.5), (42, 1.5, 0.5),
        (36, 2.0, 0.5), (42, 2.5, 0.5), (38, 3.0, 0.5), (42, 3.5, 0.5),
        (36, 4.0, 0.5), (42, 4.5, 0.5), (38, 5.0, 0.5), (42, 5.5, 0.5),
        (36, 6.0, 0.5), (42, 6.5, 0.5), (38, 7.0, 0.5), (42, 7.5, 0.5),
    ]


def test_modulo_15_build_events_guitarra_arpejo():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_guitarra() == [
        (60, 0.0, 0.5), (64, 0.5, 0.5), (67, 1.0, 0.5), (64, 1.5, 0.5),
        (65, 2.0, 0.5), (69, 2.5, 0.5), (72, 3.0, 0.5), (69, 3.5, 0.5),
        (67, 4.0, 0.5), (71, 4.5, 0.5), (74, 5.0, 0.5), (71, 5.5, 0.5),
        (60, 6.0, 0.5), (64, 6.5, 0.5), (67, 7.0, 0.5), (64, 7.5, 0.5),
    ]


def test_modulo_15_build_events_cordas_pad():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_cordas() == [
        (64, 0.0, 2.0), (67, 0.0, 2.0),
        (69, 2.0, 2.0), (72, 2.0, 2.0),
        (71, 4.0, 2.0), (74, 4.0, 2.0),
        (64, 6.0, 2.0), (67, 6.0, 2.0),
    ]
```

The drum pattern (kick=36, closed hi-hat=42, snare=38, hi-hat=42 — General
MIDI drum-map note numbers) repeats identically each 2.0s chord span, with
the kick always landing at the same instant `build_events_baixo` starts a
new note (0.0, 2.0, 4.0, 6.0) — the "lock" the README will describe. The
guitar arpeggiates each chord's root-3rd-5th-3rd at 0.5s per note (faster
than piano's blocks, contrasting with bass's sustain); the strings pad
holds only each chord's 3rd and 5th (omitting the root already covered by
bass/piano) for the full 2.0s. All verified live before this plan was
written.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_15`
Expected: 3 PASS (from Task 1) + 3 FAIL (`AttributeError: module ... has no attribute 'build_events_bateria'`, etc.)

- [ ] **Step 3: Extend `licao.py`**

First, modify the import section (right after the `sys.path.insert` line,
before `PROGRESSAO = ...`) to add:

```python
from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402
```

Then append the following to the end of the file (after `build_events_baixo`):

```python

BATERIA_PADRAO = [(36, 0.0), (42, 0.5), (38, 1.0), (42, 1.5)]  # kick-hihat-caixa-hihat


def build_events_bateria() -> list[tuple[int, float, float]]:
    """Groove rítmico: bumbo, chimbal, caixa, chimbal, repetido a cada
    acorde -- o bumbo sempre cai exatamente quando o baixo muda de nota,
    travando o groove com o baixo."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for _ in PROGRESSAO:
        for pitch_value, offset in BATERIA_PADRAO:
            events.append((pitch_value, start + offset, 0.5))
        start += 2.0
    return events


def build_events_guitarra() -> list[tuple[int, float, float]]:
    """Contraste rítmico sobre a mesma harmonia: arpejo raiz-3ª-5ª-3ª,
    mais rápido que o piano (blocos) e o baixo (sustentado)."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in PROGRESSAO:
        raiz, terca, quinta = chord
        padrao = [raiz, terca, quinta, terca]
        note_start = start
        for pitch_value in padrao:
            events.append((pitch_value, note_start, 0.5))
            note_start += 0.5
        start += 2.0
    return events


def build_events_cordas() -> list[tuple[int, float, float]]:
    """Pad de sustentação: só a 3ª e a 5ª de cada acorde (sem a
    fundamental, pra não duplicar demais o baixo/piano), sustentadas
    pelos 2 segundos inteiros."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in PROGRESSAO:
        _, terca, quinta = chord
        events.append((terca, start, 2.0))
        events.append((quinta, start, 2.0))
        start += 2.0
    return events


TRACK_NAME_VOZ = "Curso 15 - Composição e Arranjo (Voz)"
TRACK_NAME_PIANO = "Curso 15 - Composição e Arranjo (Piano)"
TRACK_NAME_BAIXO = "Curso 15 - Composição e Arranjo (Baixo)"
TRACK_NAME_BATERIA = "Curso 15 - Composição e Arranjo (Bateria)"
TRACK_NAME_GUITARRA = "Curso 15 - Composição e Arranjo (Guitarra)"
TRACK_NAME_CORDAS = "Curso 15 - Composição e Arranjo (Cordas)"


def main() -> None:
    faixas = [
        (TRACK_NAME_VOZ, build_events_voz()),
        (TRACK_NAME_PIANO, build_events_piano()),
        (TRACK_NAME_BAIXO, build_events_baixo()),
        (TRACK_NAME_BATERIA, build_events_bateria()),
        (TRACK_NAME_GUITARRA, build_events_guitarra()),
        (TRACK_NAME_CORDAS, build_events_cordas()),
    ]
    try:
        for track_name, events in faixas:
            project, _track = lesson_track(track_name)
            write_events_to_track(project, track_name, events)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print("Confira as 6 faixas no piano roll do REAPER:")
    for track_name, _ in faixas:
        print(f"  - {track_name}")
    print(
        "Motivo original (I), transposto (IV), invertido (V) e em "
        "retrógrado (I final) -- as quatro transformações clássicas de "
        "motivo, uma sobre cada acorde. Adicione um instrumento (VST) em "
        "cada faixa: veja o README para sugestões."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v -k modulo_15`
Expected: all 6 PASS

- [ ] **Step 5: Write the README**

Create `curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental/README.md`:

```markdown
# 15 — Composição e Arranjo Multi-Instrumental (Capstone)

**Referências:** todo o curso até aqui, especialmente os módulos 06
(Harmonia Funcional), 09 (Dominantes Secundárias), 10 (Condução de
Vozes), 12 (Forma Musical) — este módulo reaproveita a progressão
I-IV-V-I e o conceito de motivo transformado, aplicando tudo num arranjo
completo.

## Teoria

Compositores clássicos e populares frequentemente constroem uma peça
inteira a partir de um motivo curto (uma ideia de poucas notas),
desenvolvido através de transformações: transposição (a mesma forma em
outra altura), inversão (a mesma forma de cabeça para baixo) e
retrógrado (a mesma forma de trás para frente). Este módulo usa essas
três transformações sobre a progressão I-IV-V-I (dos módulos 06 e 12)
para compor uma peça curta, e a arranja para 6 instrumentos.

## O que o script faz

`build_events_voz()` gera a melodia: o motivo original sobre o I,
transposto sobre o IV, invertido sobre o V, e em retrógrado sobre o I
final -- as transformações são calculadas em graus de escala (não
semitons), o que garante que tudo continue dentro do tom automaticamente.
As outras cinco funções (`build_events_piano`, `build_events_baixo`,
`build_events_bateria`, `build_events_guitarra`, `build_events_cordas`)
constroem os outros instrumentos sobre a mesma harmonia. `main()` escreve
as 6 faixas no REAPER.

## Como as partes conversam

Cada instrumento tem um papel diferente, deliberadamente, para que eles
não dupliquem a mesma função:

- **Baixo** sustenta a fundamental; **Bateria** trava o groove com ele --
  o bumbo cai exatamente quando o baixo muda de nota.
- **Piano** toca a harmonia em blocos; **Guitarra** toca a mesma harmonia
  em arpejo rápido -- mesma informação harmônica, textura diferente, para
  não soarem redundantes.
- **Cordas** sustentam só a 3ª e a 5ª de cada acorde (não a fundamental,
  que já está no baixo e no piano) -- um pad que preenche sem duplicar.
- **Voz** carrega a melodia principal (o motivo e suas transformações)
  por cima de tudo isso.

## Prática com voz e teclado MIDI (opcional)

Depois de rodar o script, experimente: arme uma faixa nova no REAPER,
conecte um teclado MIDI (ou um microfone, pra cantar), aperte gravar
(usando a interface normal do REAPER -- nenhuma automação nova é
necessária aqui) e toque ou cante uma das partes que você acabou de
aprender -- por exemplo, a linha de baixo, ou a melodia da voz. Compare
o que você tocou com a versão gerada por código.

## O que esperar no piano roll

Seis faixas, todas com 8 segundos de duração, tocando juntas: uma
melodia com 4 frases de 4 notas cada (voz), acordes em bloco (piano),
notas longas graves (baixo), um padrão de bateria repetido 4 vezes,
um arpejo rápido (guitarra) e um pad de duas notas sustentadas (cordas).
Adicione um instrumento (VST) em cada faixa -- o nome do plugin depende
do que está instalado na sua máquina.
```

- [ ] **Step 6: Run test to verify it still passes and confirm the entire suite is green**

Run: `uv run pytest tests/test_curso_music21_licoes.py -v`
Expected: all PASS (módulos 01-15)

Also run the entire suite to confirm Fase 6 is fully green:

Run: `uv run pytest tests/ -v`
Expected: all PASS (212 baseline + 6 new = 218)

- [ ] **Step 7: Commit**

```bash
git add curso_music21/modulos/15_composicao_e_arranjo_multi_instrumental tests/test_curso_music21_licoes.py
git commit -m "feat: add modulo 15 - composicao e arranjo multi-instrumental (capstone)"
```

---

## After this plan

Fase 6 delivers the capstone. Only módulo 16 (bônus: Além da Tonalidade,
post-tonal/pitch-class-set topics) remains to complete the full 16-módulo
curriculum — lowest priority per the spec, and optional.
