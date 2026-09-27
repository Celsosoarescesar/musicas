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
