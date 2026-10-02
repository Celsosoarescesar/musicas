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
        (72, 0.0, 1.0), (71, 1.0, 1.0), (67, 2.0, 1.0), (69, 3.0, 1.0),
        (67, 4.0, 1.0), (71, 5.0, 1.0), (72, 6.0, 1.0),
    ]


def test_modulo_11_build_verificacao_confirma_contraponto_valido():
    licao = importlib.import_module(MODULO_11)
    assert licao.build_verificacao() is True


MODULO_12 = "curso_music21.modulos.12_forma_musical.licao"


def test_modulo_12_build_events_periodo_antecedente_e_consequente():
    licao = importlib.import_module(MODULO_12)
    assert licao.build_events() == [
        (60, 0.0, 1.0), (64, 0.0, 1.0), (67, 0.0, 1.0),
        (65, 1.0, 1.0), (69, 1.0, 1.0), (72, 1.0, 1.0),
        (67, 2.0, 1.0), (71, 2.0, 1.0), (74, 2.0, 1.0),
        (60, 3.5, 1.0), (64, 3.5, 1.0), (67, 3.5, 1.0),
        (65, 4.5, 1.0), (69, 4.5, 1.0), (72, 4.5, 1.0),
        (67, 5.5, 1.0), (71, 5.5, 1.0), (74, 5.5, 1.0),
        (60, 6.5, 1.0), (64, 6.5, 1.0), (67, 6.5, 1.0),
    ]


MODULO_13 = "curso_music21.modulos.13_musica_real_corpus_e_analise.licao"


def test_modulo_13_build_excerto_satb_com_notas_do_coral_de_bach():
    licao = importlib.import_module(MODULO_13)
    excerto = licao.build_excerto()
    dados = {
        part.partName: [
            (round(n.offset, 2), n.duration.quarterLength, n.pitch.midi)
            for n in part.flatten().notes
        ]
        for part in excerto.parts
    }
    assert dados == {
        "Soprano": [
            (0.0, 1.0, 69), (1.0, 1.0, 71), (2.0, 1.0, 73), (3.0, 1.0, 76),
            (4.0, 1.0, 73), (5.0, 1.0, 71), (6.0, 1.0, 69), (7.0, 1.0, 73),
        ],
        "Alto": [
            (0.0, 1.0, 66), (1.0, 1.0, 64), (2.0, 1.0, 64), (3.0, 1.0, 64),
            (4.0, 0.5, 64), (4.5, 0.5, 69), (5.0, 1.0, 68), (6.0, 1.0, 64),
            (7.0, 1.0, 68),
        ],
        "Tenor": [
            (0.0, 1.0, 61), (1.0, 1.0, 59), (2.0, 1.0, 57), (3.0, 1.0, 59),
            (4.0, 0.5, 57), (4.5, 0.5, 64), (5.0, 0.5, 64), (5.5, 0.5, 62),
            (6.0, 1.0, 61), (7.0, 1.0, 61),
        ],
        "Bass": [
            (0.0, 1.0, 54), (1.0, 1.0, 56), (2.0, 1.0, 57), (3.0, 1.0, 56),
            (4.0, 0.5, 57), (4.5, 0.5, 49), (5.0, 1.0, 52), (6.0, 1.0, 45),
            (7.0, 1.0, 53),
        ],
    }


def test_modulo_13_build_tonalidade_detectada_confirma_la_maior():
    licao = importlib.import_module(MODULO_13)
    assert licao.build_tonalidade_detectada() == "A major"


def test_modulo_13_build_total_corais_bach_encontra_pelo_menos_cem():
    licao = importlib.import_module(MODULO_13)
    assert licao.build_total_corais_bach() >= 100


MODULO_14 = "curso_music21.modulos.14_harmonia_popular_cifras_e_acordes_estendidos.licao"


def test_modulo_14_build_events_setimas_depois_nonas():
    licao = importlib.import_module(MODULO_14)
    assert licao.build_events() == [
        (62, 0.0, 1.0), (65, 0.0, 1.0), (69, 0.0, 1.0), (72, 0.0, 1.0),
        (67, 1.0, 1.0), (71, 1.0, 1.0), (74, 1.0, 1.0), (77, 1.0, 1.0),
        (60, 2.0, 1.0), (64, 2.0, 1.0), (67, 2.0, 1.0), (71, 2.0, 1.0),
        (62, 3.5, 1.0), (65, 3.5, 1.0), (69, 3.5, 1.0), (72, 3.5, 1.0), (76, 3.5, 1.0),
        (67, 4.5, 1.0), (71, 4.5, 1.0), (74, 4.5, 1.0), (77, 4.5, 1.0), (81, 4.5, 1.0),
        (60, 5.5, 1.0), (64, 5.5, 1.0), (67, 5.5, 1.0), (71, 5.5, 1.0), (74, 5.5, 1.0),
    ]


MODULO_15 = "curso_music21.modulos.15_composicao_e_arranjo_multi_instrumental.licao"


def test_modulo_15_build_events_voz_motivo_e_transformacoes():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_voz() == [
        (60, 0.0, 0.5), (62, 0.5, 0.5), (64, 1.0, 0.5), (60, 1.5, 0.5),
        (65, 2.0, 0.5), (67, 2.5, 0.5), (69, 3.0, 0.5), (65, 3.5, 0.5),
        (60, 4.0, 0.5), (59, 4.5, 0.5), (57, 5.0, 0.5), (60, 5.5, 0.5),
        (60, 6.0, 0.5), (64, 6.5, 0.5), (62, 7.0, 0.5), (60, 7.5, 0.5),
    ]


def test_modulo_15_build_events_piano_acordes_em_bloco():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_piano() == [
        (60, 0.0, 2.0), (64, 0.0, 2.0), (67, 0.0, 2.0),
        (65, 2.0, 2.0), (69, 2.0, 2.0), (72, 2.0, 2.0),
        (67, 4.0, 2.0), (71, 4.0, 2.0), (74, 4.0, 2.0),
        (60, 6.0, 2.0), (64, 6.0, 2.0), (67, 6.0, 2.0),
    ]


def test_modulo_15_build_events_baixo_fundamental_sustentada():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_baixo() == [
        (48, 0.0, 2.0), (53, 2.0, 2.0), (55, 4.0, 2.0), (48, 6.0, 2.0),
    ]


def test_modulo_15_build_events_bateria_kick_alinhado_com_baixo():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_bateria() == [
        (36, 0.0, 0.5), (42, 0.5, 0.5), (38, 1.0, 0.5), (42, 1.5, 0.5),
        (36, 2.0, 0.5), (42, 2.5, 0.5), (38, 3.0, 0.5), (42, 3.5, 0.5),
        (36, 4.0, 0.5), (42, 4.5, 0.5), (38, 5.0, 0.5), (42, 5.5, 0.5),
        (36, 6.0, 0.5), (42, 6.5, 0.5), (38, 7.0, 0.5), (42, 7.5, 0.5),
    ]


def test_modulo_15_build_events_guitarra_arpejo():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_guitarra() == [
        (60, 0.0, 0.5), (64, 0.5, 0.5), (67, 1.0, 0.5), (64, 1.5, 0.5),
        (65, 2.0, 0.5), (69, 2.5, 0.5), (72, 3.0, 0.5), (69, 3.5, 0.5),
        (67, 4.0, 0.5), (71, 4.5, 0.5), (74, 5.0, 0.5), (71, 5.5, 0.5),
        (60, 6.0, 0.5), (64, 6.5, 0.5), (67, 7.0, 0.5), (64, 7.5, 0.5),
    ]


def test_modulo_15_build_events_cordas_pad():
    licao = importlib.import_module(MODULO_15)
    assert licao.build_events_cordas() == [
        (64, 0.0, 2.0), (67, 0.0, 2.0),
        (69, 2.0, 2.0), (72, 2.0, 2.0),
        (71, 4.0, 2.0), (74, 4.0, 2.0),
        (64, 6.0, 2.0), (67, 6.0, 2.0),
    ]
