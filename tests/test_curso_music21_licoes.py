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


MODULO_08 = "curso_music21.modulos.08_notas_de_adorno.licao"


def test_modulo_08_build_events_esqueleto_depois_preenchida():
    licao = importlib.import_module(MODULO_08)
    assert licao.build_events() == [
        (60, 0.0, 0.5), (64, 0.5, 0.5), (67, 1.0, 0.5), (72, 1.5, 0.5),
        (60, 2.5, 0.25), (62, 2.75, 0.25), (64, 3.0, 0.25), (65, 3.25, 0.25),
        (67, 3.5, 0.25), (69, 3.75, 0.25), (71, 4.0, 0.25), (72, 4.25, 0.25),
    ]


MODULO_09 = "curso_music21.modulos.09_dominantes_secundarias_e_modulacao.licao"


def test_modulo_09_build_events_i_v_de_v_v_i():
    licao = importlib.import_module(MODULO_09)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (74, 1.0, 1.0), (78, 1.0, 1.0), (81, 1.0, 1.0),
        (67, 2.0, 1.0), (71, 2.0, 1.0), (74, 2.0, 1.0),
        (60, 3.0, 1.0), (64, 3.0, 1.0), (67, 3.0, 1.0),
    ]


MODULO_10 = "curso_music21.modulos.10_conducao_de_vozes.licao"


def test_modulo_10_build_events_superior_duas_frases_com_pausa():
    licao = importlib.import_module(MODULO_10)
    assert licao.build_events_superior() == [
        (67, 0.0, 1.0), (69, 1.0, 1.0), (67, 2.5, 1.0), (65, 3.5, 1.0),
    ]


def test_modulo_10_build_events_inferior_duas_frases_com_pausa():
    licao = importlib.import_module(MODULO_10)
    assert licao.build_events_inferior() == [
        (60, 0.0, 1.0), (62, 1.0, 1.0), (60, 2.5, 1.0), (62, 3.5, 1.0),
    ]


def test_modulo_10_build_deteccao_paralelas_confirma_problema_e_correcao():
    licao = importlib.import_module(MODULO_10)
    assert licao.build_deteccao_paralelas() == (True, False)


MODULO_11 = "curso_music21.modulos.11_contraponto.licao"


def test_modulo_11_build_events_cantus_firmus():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_events_cantus_firmus() == [
        (60, 0.0, 1.0), (62, 1.0, 1.0), (64, 2.0, 1.0), (65, 3.0, 1.0),
        (64, 4.0, 1.0), (62, 5.0, 1.0), (60, 6.0, 1.0),
    ]


def test_modulo_11_build_events_contraponto():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_events_contraponto() == [
        (72, 0.0, 1.0), (69, 1.0, 1.0), (67, 2.0, 1.0), (69, 3.0, 1.0),
        (72, 4.0, 1.0), (69, 5.0, 1.0), (72, 6.0, 1.0),
    ]


def test_modulo_11_build_verificacao_confirma_contraponto_valido():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_verificacao() is True
