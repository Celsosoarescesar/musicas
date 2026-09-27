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
