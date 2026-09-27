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
