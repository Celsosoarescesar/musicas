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


MODULO_04 = "curso_music21.modulos.04_intervalos.licao"


def test_modulo_04_build_pitches_root_then_each_interval():
    licao = importlib.import_module(MODULO_04)
    assert licao.build_pitches() == [60, 60, 64, 67, 72]


MODULO_05 = "curso_music21.modulos.05_acordes_e_triades.licao"


def test_modulo_05_build_events_four_triad_qualities_on_same_root():
    licao = importlib.import_module(MODULO_05)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (60, 1.0, 1.0), (63, 1.0, 1.0), (67, 1.0, 1.0),
        (60, 2.0, 1.0), (63, 2.0, 1.0), (66, 2.0, 1.0),
        (60, 3.0, 1.0), (64, 3.0, 1.0), (68, 3.0, 1.0),
    ]


MODULO_06 = "curso_music21.modulos.06_harmonia_funcional_numerais_romanos.licao"


def test_modulo_06_build_events_progressao_i_iv_v_i():
    licao = importlib.import_module(MODULO_06)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (65, 1.0, 1.0), (69, 1.0, 1.0), (72, 1.0, 1.0),
        (67, 2.0, 1.0), (71, 2.0, 1.0), (74, 2.0, 1.0),
        (60, 3.0, 1.0), (64, 3.0, 1.0), (67, 3.0, 1.0),
    ]


MODULO_07 = "curso_music21.modulos.07_cadencias_e_modelo_de_frase.licao"


def test_modulo_07_build_events_quatro_cadencias_com_pausas():
    licao = importlib.import_module(MODULO_07)
    assert licao.build_events() == [
        (67, 0.0, 1.0), (71, 0.0, 1.0), (74, 0.0, 1.0),
        (60, 1.0, 1.0), (64, 1.0, 1.0), (67, 1.0, 1.0),
        (60, 2.5, 1.0), (64, 2.5, 1.0), (67, 2.5, 1.0),
        (67, 3.5, 1.0), (71, 3.5, 1.0), (74, 3.5, 1.0),
        (65, 5.0, 1.0), (69, 5.0, 1.0), (72, 5.0, 1.0),
        (60, 6.0, 1.0), (64, 6.0, 1.0), (67, 6.0, 1.0),
        (67, 7.5, 1.0), (71, 7.5, 1.0), (74, 7.5, 1.0),
        (69, 8.5, 1.0), (72, 8.5, 1.0), (76, 8.5, 1.0),
    ]
