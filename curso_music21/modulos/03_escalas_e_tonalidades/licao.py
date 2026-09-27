"""Lição 03 - Escalas e Tonalidades."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import generate_scale, write_notes_to_track  # noqa: E402

TRACK_NAME = "Curso 03 - Escalas e Tonalidades"


def build_pitches() -> list[int]:
    """Escala de Do maior seguida da escala de La menor natural (relativa) --
    mesmas notas, tonalidades diferentes."""
    return generate_scale("C", "major") + generate_scale("A", "natural_minor")


def main() -> None:
    pitches = build_pitches()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_notes_to_track(project, TRACK_NAME, pitches, note_length=0.25)
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
        "Primeira metade: escala de Do maior. Segunda metade: escala de La "
        "menor natural -- mesmas sete notas, tonalidades diferentes."
    )


if __name__ == "__main__":
    main()
