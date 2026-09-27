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
