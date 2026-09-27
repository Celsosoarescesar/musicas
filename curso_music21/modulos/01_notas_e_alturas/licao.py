"""Lição 01 - Notas e Alturas."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import pitch  # noqa: E402

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_notes_to_track  # noqa: E402

TRACK_NAME = "Curso 01 - Notas e Alturas"


def build_pitches() -> list[int]:
    """C em quatro oitavas (mesma classe de nota, alturas diferentes),
    seguido dos nomes de nota de Do a Si numa só oitava (classes diferentes)."""
    same_pitch_class = [pitch.Pitch(f"C{octave}").midi for octave in range(2, 6)]
    different_pitch_classes = [
        pitch.Pitch(f"{name}4").midi for name in ["C", "D", "E", "F", "G", "A", "B"]
    ]
    return same_pitch_class + different_pitch_classes


def main() -> None:
    pitches = build_pitches()
    try:
        project, _track = lesson_track(TRACK_NAME)
        write_notes_to_track(project, TRACK_NAME, pitches, note_length=0.5)
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
        "As quatro primeiras notas são todas 'Do' (C) em oitavas diferentes "
        "-- mesma classe de nota. As sete seguintes são notas diferentes na "
        "mesma oitava."
    )


if __name__ == "__main__":
    main()
