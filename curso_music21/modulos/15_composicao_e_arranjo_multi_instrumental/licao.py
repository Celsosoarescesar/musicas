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
