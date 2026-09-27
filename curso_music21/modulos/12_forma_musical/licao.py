"""Lição 12 - Forma Musical."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_progression, write_events_to_track  # noqa: E402

TRACK_NAME = "Curso 12 - Forma Musical"


def build_events() -> list[tuple[int, float, float]]:
    """Um período clássico: frase antecedente (I-IV-V, termina em meia
    cadência -- a 'pergunta') seguida, após uma pausa, da frase
    consequente (I-IV-V-I, termina em cadência autêntica -- a
    'resposta'). As duas frases compartilham a mesma abertura e só se
    diferenciam no final."""
    antecedente = generate_progression("C", ["I", "IV", "V"])
    consequente = generate_progression("C", ["I", "IV", "V", "I"])
    events: list[tuple[int, float, float]] = []
    start = 0.0
    for chord in antecedente:
        for pitch_value in chord:
            events.append((pitch_value, start, 1.0))
        start += 1.0
    start += 0.5
    for chord in consequente:
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
        "Frase antecedente (I-IV-V, 'pergunta', termina em aberto) seguida "
        "da frase consequente (I-IV-V-I, 'resposta', termina resolvida) -- "
        "um período clássico."
    )


if __name__ == "__main__":
    main()
