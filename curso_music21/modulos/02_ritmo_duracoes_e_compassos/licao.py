"""Lição 02 - Ritmo: Durações e Compassos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 02 - Ritmo: Duracoes e Compassos"
SECONDS_PER_QUARTER = 0.5  # 120 bpm


def build_events() -> list[tuple[int, float, float]]:
    """Semibreve, mínima, semínima e colcheia em sequência, todas na mesma
    altura (C4), para comparar duração sem a variável de altura mudando."""
    quarter_lengths = [4.0, 2.0, 1.0, 0.5]
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for quarter_length in quarter_lengths:
        duration = quarter_length * SECONDS_PER_QUARTER
        events.append((60, start, duration))
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
        "Quatro notas na mesma altura, cada uma com metade da duração da "
        "anterior: semibreve, mínima, semínima, colcheia."
    )


if __name__ == "__main__":
    main()
