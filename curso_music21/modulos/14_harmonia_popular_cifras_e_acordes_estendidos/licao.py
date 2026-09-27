"""Lição 14 - Harmonia Popular: Cifras e Acordes Estendidos."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 14 - Harmonia Popular (Cifras e Acordes Estendidos)"


def build_events() -> list[tuple[int, float, float]]:
    """A progressão ii-V-I (ii7-V7-IMaj7, a cadência mais comum do jazz)
    seguida, após uma pausa, da mesma progressão com acordes estendidos
    (ii9-V9-IM9) -- mesma harmonia, mais cor."""
    setimas = generate_progression("C", ["ii7", "V7", "IMaj7"])
    nonas = generate_progression("C", ["ii9", "V9", "IM9"])
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in setimas:
        for pitch_value in chord:
            events.append((pitch_value, start, 1.0))
        start += 1.0
    start += 0.5
    for chord in nonas:
        for pitch_value in chord:
            events.append((pitch_value, start, 1.0))
        start += 1.0
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
        "ii7-V7-IMaj7 (sétimas) seguido de ii9-V9-IM9 (nonas) -- a mesma "
        "progressão funcional, com acordes estendidos (a nona adicionada)."
    )


if __name__ == "__main__":
    main()
