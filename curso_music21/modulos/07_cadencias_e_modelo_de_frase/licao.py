"""Lição 07 - Cadências e Modelo de Frase."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 07 - Cadencias e Modelo de Frase"

CADENCIAS = [
    ("autentica", ["V", "I"]),
    ("meia_cadencia", ["I", "V"]),
    ("plagal", ["IV", "I"]),
    ("deceptiva", ["V", "vi"]),
]


def build_events() -> list[tuple[int, float, float]]:
    """Quatro cadências de dois acordes em Do maior, tocadas em sequência
    com uma pausa entre elas: autêntica (V-I), meia-cadência (I-V),
    plagal (IV-I) e deceptiva (V-vi) -- para comparar o grau de repouso
    de cada uma."""
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for _, numerals in CADENCIAS:
        progression = generate_progression("C", numerals)
        for chord in progression:
            for pitch_value in chord:
                events.append((pitch_value, start, 1.0))
            start += 1.0
        start += 0.5
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
        "Quatro cadencias em sequencia, separadas por uma pausa: autentica "
        "(V-I, repouso total), meia-cadencia (I-V, fica em aberto), plagal "
        "(IV-I, o 'amem'), deceptiva (V-vi, surpresa -- nao resolve na tonica)."
    )


if __name__ == "__main__":
    main()
