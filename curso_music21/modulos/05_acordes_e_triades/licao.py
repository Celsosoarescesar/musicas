"""Lição 05 - Acordes e Tríades."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_chord, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 05 - Acordes e Triades"
QUALIDADES = ["major", "minor", "diminished", "augmented"]


def build_events() -> list[tuple[int, float, float]]:
    """As quatro tríades clássicas sobre a mesma fundamental (Do), uma de
    cada vez, para comparar a qualidade do acorde."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    duration = 1.0
    for quality in QUALIDADES:
        for pitch_value in generate_chord(60, quality):
            events.append((pitch_value, start, duration))
        start += duration
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
        "Quatro tríades sobre Do: maior, menor, diminuta, aumentada -- "
        "compare como a terça e a quinta mudam de posição a cada uma."
    )


if __name__ == "__main__":
    main()
