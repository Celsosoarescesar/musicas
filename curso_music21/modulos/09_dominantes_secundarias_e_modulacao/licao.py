"""Lição 09 - Dominantes Secundárias e Modulação."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 09 - Dominantes Secundarias e Modulacao"


def build_events() -> list[tuple[int, float, float]]:
    """I - V/V - V - I em Do maior: o V/V (dominante da dominante)
    tonaciza o V por um instante antes de resolver -- um gostinho de
    modulação sem sair de fato da tonalidade."""
    progression = generate_progression("C", ["I", "V/V", "V", "I"])
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
        "I - V/V - V - I: o segundo acorde 'pisca' na tonalidade de Sol "
        "(a dominante de Sol) antes de resolver no V de verdade."
    )


if __name__ == "__main__":
    main()
