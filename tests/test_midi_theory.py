import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import analyze_notes, generate_chord, generate_progression, generate_scale


def test_generate_scale_c_major_returns_expected_midi_pitches():
    pitches = generate_scale("C", "major")
    assert pitches[:8] == [48, 50, 52, 53, 55, 57, 59, 60]


def test_generate_scale_raises_for_unknown_scale_type():
    with pytest.raises(ReaperBridgeError, match="não suportada"):
        generate_scale("C", "lidian_invalido")


def test_generate_chord_c_major_returns_root_third_fifth():
    assert generate_chord(60, "major") == [60, 64, 67]


def test_generate_chord_raises_for_unknown_quality():
    with pytest.raises(ReaperBridgeError, match="não suportado"):
        generate_chord(60, "quality_invalida")


def test_generate_progression_ii_v_i_in_c_returns_three_chords():
    progression = generate_progression("C", ["ii", "V", "I"])
    assert len(progression) == 3
    assert progression[2] == [60, 64, 67]  # I em Do maior = C4 E4 G4


def test_generate_progression_raises_for_invalid_key():
    with pytest.raises(ReaperBridgeError, match="inválida"):
        generate_progression("chave_invalida_123", ["I"])


def test_analyze_notes_detects_c_major_chord():
    result = analyze_notes([60, 64, 67])
    assert "C" in result


def test_analyze_notes_raises_for_empty_input():
    with pytest.raises(ReaperBridgeError, match="nenhuma nota"):
        analyze_notes([])
