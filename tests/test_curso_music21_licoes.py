import importlib

MODULO_01 = "curso_music21.modulos.01_notas_e_alturas.licao"


def test_modulo_01_build_pitches_same_class_then_different_classes():
    licao = importlib.import_module(MODULO_01)
    assert licao.build_pitches() == [36, 48, 60, 72, 60, 62, 64, 65, 67, 69, 71]
