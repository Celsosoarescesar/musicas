# Curso de Música com music21 no piano roll do REAPER

## Contexto e motivação

O projeto `reaper-copilot` já previa, desde o spec original, usar "o piano
roll do REAPER como ferramenta de aprendizado musical (gerar e analisar
exercícios com teoria via `music21`)". Este spec detalha esse pedaço:
um curso de teoria musical e composição onde cada lição gera conteúdo com
`music21` e escreve no piano roll de uma sessão REAPER aberta, para que o
aprendizado aconteça vendo/ouvindo (e depois tocando) a teoria, em vez de
só lendo texto ou rodando código isolado.

O material teórico de cada lição combina duas referências:

- **music21 User's Guide** (https://music21.org/music21docs/usersGuide/) —
  como programar cada conceito (notas, streams, análise, corpus).
- **Open Music Theory** (https://viva.pressbooks.pub/openmusictheory/,
  Creative Commons, atribuição obrigatória) — o que o conceito significa
  musicalmente (escalas, cadências, condução de vozes, forma, contraponto).
  O curso linka e resume esses capítulos com as próprias palavras; não
  copia o texto do livro.

O `reaper_bridge` (usado hoje pelo MCP server `reaper-copilot`) já expõe
boa parte do necessário: `generate_scale`, `generate_chord`,
`generate_progression`, `analyze_notes`, `write_notes_to_track` (em
`midi.py`), `add_fx` (em `mixing.py`), `get_project` (em `connection.py`),
e um fake de projeto REAPER para testes (`tests/fakes.py`). O curso reusa
esse código em vez de duplicar lógica de reapy/music21.

## Fora de escopo

- **Trilha separada sobre a API interna do music21** (streams avançados,
  configuração de ambiente, extensão de conversor, sites/contexts, etc.)
  — considerada e descartada; o curso cobre só o necessário do music21
  para construir as lições de música, não a biblioteca por si mesma.
- **Automatizar a gravação de voz/teclado MIDI.** Gravar é uma performance
  ao vivo do usuário; as lições de prática apenas instruem (no README) a
  armar a faixa e gravar usando a interface normal do REAPER. Nenhum
  código novo de arm/record/input-monitoring é criado por este projeto.
- **Recomendar ou instalar plugins/instrumentos VST específicos.** O
  módulo de composição multi-instrumental orienta que tipo de instrumento
  colocar em cada faixa (bateria, baixo, cordas, etc.) e reusa a tool
  `reaper_add_fx` já existente para adicionar o plugin pelo nome exato,
  mas não lista nem instala plugins — depende do que já está instalado
  na máquina do usuário.
- **Interface própria (web/CLI) para navegar o curso.** As lições são
  scripts Python + README em markdown, rodados diretamente pelo usuário;
  não há um "app do curso".

## Arquitetura

```
curso_music21/
  README.md                    # índice do curso, pré-requisitos
  _shared/
    reaper_track.py            # lesson_track(name) -> (project, track)
  modulos/
    01_notas_e_alturas/
      README.md
      licao.py
    02_ritmo_duracoes_e_compassos/
    03_escalas_e_tonalidades/
    04_intervalos/
    05_acordes_e_triades/
    06_harmonia_funcional_numerais_romanos/
    07_cadencias_e_modelo_de_frase/
    08_notas_de_adorno/
    09_dominantes_secundarias_e_modulacao/
    10_conducao_de_vozes/
    11_contraponto/
    12_forma_musical/
    13_musica_real_corpus_e_analise/
    14_harmonia_popular_cifras_e_acordes_estendidos/
    15_composicao_e_arranjo_multi_instrumental/
    16_bonus_alem_da_tonalidade/
```

Cada pasta de lição contém:

- `README.md`: teoria (com link/resumo do capítulo correspondente do
  music21 user guide e/ou do Open Music Theory), o que o script faz, e o
  que esperar ver/ouvir no piano roll do REAPER.
- `licao.py`: script executável, rodado com `python
  curso_music21/modulos/NN_.../licao.py` com o REAPER já aberto.

### Padrão de `licao.py`

Cada script separa lógica pura (testável sem REAPER) de I/O com o REAPER:

```python
"""Lição NN - <título>."""
from curso_music21._shared.reaper_track import lesson_track
from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import write_notes_to_track  # ou write_events_to_track /
                                                       # write_score_to_tracks

TRACK_NAME = "Curso NN - <título>"


def build_pitches() -> list[int]:
    """Lógica pura com music21 — testável sem REAPER aberto."""
    ...


def main() -> None:
    pitches = build_pitches()
    try:
        project, track = lesson_track(TRACK_NAME)
        write_notes_to_track(project, TRACK_NAME, pitches)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(f"Confira a faixa '{TRACK_NAME}' no piano roll do REAPER.")


if __name__ == "__main__":
    main()
```

### `_shared/reaper_track.py`

```python
def lesson_track(name: str) -> tuple[reapy.Project, "reapy.Track"]:
    """Conecta ao REAPER (get_project) e garante uma faixa dedicada e limpa
    para a lição, criando-a se não existir e limpando itens se já existir
    (idempotente ao rodar a lição de novo)."""
```

Reusa `reaper_bridge.connection.get_project`,
`reaper_bridge.project.find_track` / `create_track`, e uma nova função
`clear_track_items` (ver abaixo).

## Extensões necessárias em `reaper_bridge`

Funções novas, reusáveis fora do curso (não é código exclusivo dele):

- **`project.clear_track_items(track)`** — remove os itens MIDI existentes
  de uma faixa, usada por `lesson_track` para tornar as lições idempotentes
  ao rodar de novo.
- **`midi.write_events_to_track(project, track_name, events, velocity=100)`**
  — `events: list[tuple[int, float, float]]` = `(pitch, start, duration)`
  por nota, para ritmo variável. Necessária a partir do módulo 02 (Ritmo),
  usada também pelo 13 (Corpus/Bach) e 15 (Composição). `write_notes_to_track`
  (duração fixa) continua existindo e sendo usada pelas lições mais simples
  (escalas, intervalos, acordes isolados).
- **`midi.write_score_to_tracks(project, score, track_prefix="")`** — recebe
  um `music21.stream.Score` com várias partes (ex: coral SATB do corpus de
  Bach, ou melodia/baixo/cordas do capstone) e escreve cada parte em uma
  faixa separada do REAPER, nomeada a partir de `track_prefix` + o nome/índice
  da parte. Usada pelos módulos 13 e 15.

O módulo 13 (Corpus) usa `music21.corpus.parse(...)` diretamente — já vem
com o music21, sem código novo — e passa o `Score` resultante para
`write_score_to_tracks`.

O módulo 15 (capstone) usa `write_score_to_tracks` para montar as faixas
(bateria, baixo, guitarra, piano, cordas, voz) e reusa
`reaper_bridge.mixing.add_fx` (já existe) para adicionar um instrumento a
cada faixa.

## Currículo (16 módulos)

| # | Módulo | Referência |
|---|---|---|
| 01 | Notas e Alturas | music21 caps. 2-3 / OMT Pitch |
| 02 | Ritmo: Durações e Compassos | music21 caps. 3,14,19,27 / OMT Rhythm & Meter |
| 03 | Escalas e Tonalidades | `reaper_bridge.midi.generate_scale` / OMT Scales |
| 04 | Intervalos | music21 cap. 18 / OMT Intervals |
| 05 | Acordes e Tríades | music21 caps. 7,9 / OMT Triads/7ths |
| 06 | Harmonia Funcional (Numerais Romanos) | music21 cap. 23 / OMT Roman Numerals |
| 07 | Cadências e Modelo de Frase (T-PD-D-T) | OMT Cadences |
| 08 | Notas de Adorno (non-chord tones) | OMT Embellishing Tones |
| 09 | Dominantes Secundárias e Modulação | OMT Tonicization/Modulation |
| 10 | Condução de Vozes | OMT Voice Leading |
| 11 | Contraponto (species counterpoint) | OMT Counterpoint — prepara para o módulo 13 |
| 12 | Forma Musical | OMT Form |
| 13 | Música Real: Corpus e Análise (Bach etc.) | music21 caps. 11,53 |
| 14 | Harmonia Popular / Cifras e Acordes Estendidos | OMT Popular Music |
| 15 | Composição e Arranjo Multi-Instrumental (capstone) | tudo dos módulos 01-14 |
| 16 | Bônus: Além da Tonalidade | music21 cap. 25 / OMT Post-Tonal |

### Módulo 07 — ressalva de implementação

A ideia original incluía checar automaticamente quintas/oitavas paralelas
via music21. Isso **precisa ser validado durante a implementação** (a
API pode ou não cobrir isso de forma direta); se não houver suporte nativo
adequado, a lição cai para comparação manual/visual no piano roll em vez
de checagem automática — decisão a ser tomada na hora, não prometida aqui.

### Módulo 15 — detalhamento

Capstone: compor uma peça curta original (motivo + forma, dos módulos
anteriores) e arranjá-la em várias faixas/instrumentos do REAPER:

- **Bateria** — padrão rítmico/groove.
- **Baixo** — linha de baixo seguindo a harmonia (módulos 06/09).
- **Guitarra** — harmoniza os acordes ou faz contramelodia, contrastando
  deliberadamente com o que o baixo está fazendo (ex: quando o baixo faz
  uma linha melódica, a guitarra assume papel harmônico diferente).
- **Piano/teclado** — acompanhamento harmônico (comping).
- **Cordas de orquestra** (violino, viola, violoncelo) — pad ou
  contramelodia.
- **Voz** — melodia principal.

Cada faixa recebe um instrumento via `reaper_add_fx` (nome do plugin
depende do que está instalado). O README da lição discute explicitamente
como as partes conversam entre si (papéis complementares, evitar
duplicação de função entre instrumentos, como bateria e baixo travam o
groove juntos).

**Prática com voz e teclado MIDI**: parte opcional da lição — armar uma
faixa, conectar teclado MIDI ou microfone, gravar (usando a interface
nativa do REAPER, sem automação nova) uma parte que o usuário acabou de
aprender (ex.: tocar a linha de baixo ele mesmo, ou cantar a melodia),
comparando com a versão gerada por código.

## Testes

- Funções `build_*()` de cada lição: testadas como funções puras, mesmo
  padrão de `tests/test_midi_theory.py`.
- `write_events_to_track` e `write_score_to_tracks`: testadas contra o
  fake de projeto já existente em `tests/fakes.py`, mesmo padrão de
  `tests/test_midi_track.py`.
- Os próprios `licao.py` (a função `main()`) não têm teste automatizado
  de ponta a ponta — dependem de REAPER aberto de verdade; são scripts de
  demonstração, não código testado por CI.

## Tratamento de erros

Reusa `ReaperBridgeError` (já existente) e a mensagem de timeout já
produzida por `get_project()`. Cada `licao.py` captura `ReaperBridgeError`
em `main()` e imprime uma mensagem em PT-BR orientando abrir o REAPER e
confirmar a configuração do reapy — sem stack trace cru para o usuário.

## Ordem de entrega

16 módulos é muito para uma leva só. A implementação é dividida em fases
no plano (a ser escrito em seguida via `writing-plans`), aproximadamente:

1. Infraestrutura compartilhada (`_shared/`, extensões em `reaper_bridge`)
   + módulos 01-05 (fundamentos).
2. Módulos 06-09 (harmonia funcional e suas extensões).
3. Módulos 10-12 (condução de vozes, contraponto, forma).
4. Módulo 13 (corpus/Bach) + 14 (harmonia popular).
5. Módulo 15 (capstone) + 16 (bônus).

A ordem exata das fases e como elas viram tarefas fica a cargo do plano de
implementação.
