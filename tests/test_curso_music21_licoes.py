import importlib

MODULO_01 = "curso_music21.modulos.01_notas_e_alturas.licao"
MODULO_02 = "curso_music21.modulos.02_ritmo_duracoes_e_compassos.licao"
MODULO_03 = "curso_music21.modulos.03_escalas_e_tonalidades.licao"


def test_modulo_01_build_pitches_same_class_then_different_classes():
    licao = importlib.import_module(MODULO_01)
    assert licao.build_pitches() == [36, 48, 60, 72, 60, 62, 64, 65, 67, 69, 71]


def test_modulo_02_build_events_halves_duration_each_step():
    licao = importlib.import_module(MODULO_02)
    assert licao.build_events() == [
        (60, 0.0, 2.0),
        (60, 2.0, 1.0),
        (60, 3.0, 0.5),
        (60, 3.5, 0.25),
    ]


def test_modulo_03_build_pitches_c_major_then_a_natural_minor():
    licao = importlib.import_module(MODULO_03)
    assert licao.build_pitches() == [
        48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72,
        57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81,
    ]
