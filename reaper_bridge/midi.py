from __future__ import annotations

from music21 import chord as m21chord
from music21 import key as m21key
from music21 import note as m21note
from music21 import roman as m21roman
from music21 import scale as m21scale
from music21 import stream as m21stream

from .errors import ReaperBridgeError
from .project import find_track

SCALE_TYPES = {
    "major": m21scale.MajorScale,
    "natural_minor": m21scale.MinorScale,
    "harmonic_minor": m21scale.HarmonicMinorScale,
    "melodic_minor": m21scale.MelodicMinorScale,
    "dorian": m21scale.DorianScale,
    "mixolydian": m21scale.MixolydianScale,
}

CHORD_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
}


def generate_scale(root: str, scale_type: str) -> list[int]:
    scale_class = SCALE_TYPES.get(scale_type)
    if scale_class is None:
        raise ReaperBridgeError(
            f"escala '{scale_type}' não suportada, opções: {', '.join(SCALE_TYPES)}"
        )
    try:
        generated = scale_class(root)
        pitches = generated.getPitches(f"{root}3", f"{root}5")
    except Exception as exc:
        raise ReaperBridgeError(f"nota '{root}' inválida para gerar escala") from exc
    return [p.midi for p in pitches]


def generate_chord(root_midi: int, quality: str) -> list[int]:
    intervals = CHORD_INTERVALS.get(quality)
    if intervals is None:
        raise ReaperBridgeError(
            f"tipo de acorde '{quality}' não suportado, opções: {', '.join(CHORD_INTERVALS)}"
        )
    return [root_midi + interval for interval in intervals]


def generate_progression(key_name: str, numerals: list[str]) -> list[list[int]]:
    try:
        detected_key = m21key.Key(key_name)
    except Exception as exc:
        raise ReaperBridgeError(f"tonalidade '{key_name}' inválida") from exc
    progression = []
    for numeral in numerals:
        try:
            rn = m21roman.RomanNumeral(numeral, detected_key)
        except Exception as exc:
            raise ReaperBridgeError(
                f"grau '{numeral}' inválido para a tonalidade '{key_name}'"
            ) from exc
        progression.append([p.midi for p in rn.pitches])
    return progression


def analyze_notes(midi_pitches: list[int]) -> str:
    if not midi_pitches:
        raise ReaperBridgeError("nenhuma nota MIDI para analisar")
    notes = [m21note.Note(midi=pitch) for pitch in midi_pitches]
    detected_key = m21stream.Stream(notes).analyze("key")
    chord_obj = m21chord.Chord(notes)
    return (
        f"Tonalidade mais provável: {detected_key.tonic.name} {detected_key.mode}. "
        f"Acorde formado pelas notas: {chord_obj.pitchedCommonName}."
    )


def write_notes_to_track(
    project,
    track_name: str,
    pitches: list[int],
    start: float = 0.0,
    note_length: float = 0.5,
    velocity: int = 100,
):
    if not pitches:
        raise ReaperBridgeError("nenhuma nota para escrever no piano roll")
    track = find_track(project, track_name)
    end = start + note_length * len(pitches)
    try:
        item = track.add_midi_item(start=start, end=end)
        take = item.active_take
        for index, pitch_value in enumerate(pitches):
            note_start = start + index * note_length
            take.add_note(
                start=note_start,
                end=note_start + note_length,
                pitch=pitch_value,
                velocity=velocity,
                unit="seconds",
            )
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível escrever as notas no piano roll: verifique se o REAPER está aberto"
        ) from exc
    return item


def read_notes_from_track(project, track_name: str) -> list[int]:
    track = find_track(project, track_name)
    try:
        pitches = []
        for item in track.items:
            take = item.active_take
            if take is None or not take.is_midi:
                continue
            pitches.extend(note.pitch for note in take.notes)
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível ler as notas do piano roll: verifique se o REAPER está aberto"
        ) from exc
    return pitches
