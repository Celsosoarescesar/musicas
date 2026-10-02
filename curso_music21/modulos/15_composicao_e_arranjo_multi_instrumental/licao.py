"""Lição 15 - Composição e Arranjo Multi-Instrumental (capstone)."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402

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
