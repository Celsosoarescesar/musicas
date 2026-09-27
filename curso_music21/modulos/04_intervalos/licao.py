"""Lição 04 - Intervalos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import interval, pitch  # noqa: E402

from curso_music21._shared.reaper_track import lesson_track  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_notes_to_track  # noqa: E402

TRACK_NAME = "Curso 04 - Intervalos"
INTERVALOS = ["P1", "M3", "P5", "P8"]


def build_pitches() -> list[int]:
    """Nota fundamental seguida de cada intervalo aplicado sobre ela, para
    ouvir a distância entre eles."""
    root = pitch.Pitch("C4")
    pitches = [root.midi]
    for name in INTERVALOS:
        iv = interval.Interval(name)
        pitches.append(iv.transposePitch(root).midi)
    return pitches


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
        "Fundamental, uníssono (mesma nota), terça maior, quinta justa e "
        "oitava -- todos acima da mesma fundamental (Do4)."
    )


if __name__ == "__main__":
    main()
