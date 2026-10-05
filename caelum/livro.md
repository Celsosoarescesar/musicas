# Caelum -- o livro e a vida (album de 21 faixas)

**Spec:** `docs/superpowers/specs/2026-10-05-caelum-album-livro-e-vida-design.md`. A vida real do
autor (faixas V) esta em `conceito.md` e no spec de 2026-10-04; o arco de Caelum (faixas M) vem da
biblia de 2026-10-03.

## A ideia (estilo Assassin's Creed)

O autor, hoje, encontra um livro antigo sobre Caelum, um executor medieval da **Ordem Grave**, e
transforma esse livro em musica. Duas historias que se espelham:

- **V (a vida):** a vida real do autor. Nu metal, sem orquestra. As 11 pastas `NN_*` (10 do arco +
  a 11, Obedecer).
- **M (o livro):** a historia de Caelum medieval, em primeira pessoa e sem narrador. Nu metal
  sinfonico: a mesma banda mais orquestra e coral. As 10 pastas `mNN_*`.

A voz e sempre a do autor. "Caelum" e o artista, o personagem do livro e o titulo das duas ultimas
faixas.

## Ordem do disco (21 faixas)

Cada V e seguida da M que espelha o mesmo sentimento; a 11 entra antes do Executor. V e M do mesmo
par usam o mesmo tom e bpm, **exceto nos pares 3 e 7** (V3 E/112 e V7 E/88; M3 E/88 e M7 F#/112).

| # | Pasta | Tipo | Titulo | Tom / bpm | O espelho |
|---|---|---|---|---|---|
| 1 | `01_sozinho` | V | Sozinho | D / 100 | Solidao; o autor acha o livro |
| 2 | `m01_quebra_de_fe` | M | Quebra de fe | D / 100 | A verdade que ninguem quer ouvir |
| 3 | `02_rotina` | V | Rotina | A / 96 | Moto todo dia, piloto automatico |
| 4 | `11_obedecer` | V | Obedecer | A / 96 | Obedecer calado (a faixa da igreja) |
| 5 | `m02_executor` | M | Executor | A / 96 | Cumprir ordens sem perguntar |
| 6 | `03_o_que_nao_veio` | V | Nunca foi lar | E / 112 | A casa que nao foi lar |
| 7 | `m03_silencio` | M | Silencio | E / 88 | Ignorar os sinais para nao perder a fe |
| 8 | `04_barulho` | V | Barulho | B / 108 | A montanha: eu nao morro aqui |
| 9 | `m04_a_mao_que_me_fez` | M | A mao que me fez | B / 108 | Raiva de quem o moldou |
| 10 | `05_vazio` | V | Vazio | F# / 92 | O afogamento |
| 11 | `m05_culpa` | M | Culpa | F# / 92 | Cada monstro tinha um rosto |
| 12 | `06_tempo_perdido` | V | Tempo perdido | C# / 120 | Por que obedeci calado? |
| 13 | `m06_revolta` | M | Revolta | C# / 120 | Rompe com a Ordem |
| 14 | `07_silencio` | V | Silencio (quem me entenda) | E / 88 | Ser entendido |
| 15 | `m07_do_outro_lado` | M | Do outro lado | F# / 112 | Os monstros que o entendem |
| 16 | `08_recomeco` | V | Recomeco | B / 98 | O vento leva a minha voz |
| 17 | `m08_monstros` | M | Monstros | B / 98 | A virada: o monstro e quem controla o sistema |
| 18 | `09_tarde_demais` | V | Tarde demais | E / 104 | As quatro estacoes |
| 19 | `m09_fora_do_sistema` | M | Fora do sistema | E / 104 | Ser julgado por quem ficou |
| 20 | `10_caelum` | V | Caelum | D / 100 | Os passaros e o ceu |
| 21 | `m10_caelum` | M | Caelum | D / 100 | As duas historias se encontram no ceu |

## A historia de Caelum no livro

Tres atos. Caelum e executor da Ordem Grave e cumpre ordens sem questionar. Descobre que a Igreja
fabrica os monstros que ele matava, rompe, se junta aos monstros e e julgado. Final do album 1:
caminho do meio (a Ordem continua de pe; Caelum vive livre fora dela).

| Ato | Faixas M | Cena | "Monstro" quer dizer |
|---|---|---|---|
| Fe | M01-M03 | Descobre a verdade; orgulho de executar; ignora os sinais | Obra da Ordem; o que a Ordem manda executar |
| Ruptura | M04-M07 | Raiva, culpa, rompimento, alianca com os monstros | A mao que cria merece o nome; os monstros tinham rosto |
| Nova realidade | M08-M10 | A virada, o julgamento, o encontro com o ceu | O monstro e quem controla o sistema |

Dois eixos: **obediencia sem questionar** e **quem e o monstro**. Mantra da Ordem:
**"Obey. Don't ask."** sussurrado nas M01-M03, **invertido** ("Ask. Don't obey.") nas M08-M10;
gravado com a voz do autor na camada REAPER.

## Som

**V:** guitarras de 7 cordas afinadas baixo, verso baixo, refrao limpo, grito quando o sentimento
pede; sem orquestra.

**M:** a mesma banda mais orquestra. O prompt de cada M diz "symphonic nu metal" e a orquestra do ato:

| Ato | Orquestra (palavras do prompt) | Sensacao |
|---|---|---|
| Fe | pipe organ, low liturgical choir, restrained strings | O som da Ordem: solene, frio, menor harmonica |
| Ruptura | tremolo strings, brass stabs, timpani | A orquestra vira ameaca e depois se rompe |
| Nova realidade | open soaring strings, rising choir | O som da Ordem volta transformado em saida e esperanca |

Cada M abre com som de livro (folha, pena na tinta); a V nao. Na faixa final (`m10_caelum`, a 21),
a banda do V e a orquestra do M tocam juntas.

**Limite:** o ACE-Step ainda nao foi testado com orquestra. Antes de escrever as outras 9 letras M,
gerar so a M01 (Quebra de fe) em 3 ou 4 tentativas (seeds e variacoes de prompt); se o sinfonico nao
soar, ajustar o prompt e, se preciso, mover a orquestra para a camada REAPER (MIDI e instrumentos
virtuais, trabalho manual do autor).

## Fluxo de cada faixa M

1. Cena e imagem combinadas com o autor (propor 3-4 imagens com um verso de exemplo e recomendacao).
2. Letra PT (poetica, metaforica, uma imagem unica; fonte da verdade). 3. Aprovacao.
4. EN (silabas que cabem na melodia) + pronuncia em PT-BR; tirar o slug de `UNWRITTEN` em
   `tests/test_caelum_biblia.py`. 5. Testes. 6. Geracao: `uv run python scripts/caelum_gerar.py m01_quebra_de_fe`.
7. Stems depois, so se gostar. 8. O autor grava a voz e faz mix/master; merge unico na `main`
   depois (decisao dele).

## Regras

- Primeira pessoa, uma imagem unica por faixa, linhas curtas (ate 10 silabas), sem narrador.
- M e alegoria medieval: nada de pessoas, igrejas ou partidos reais; critica o MECANISMO de
  controle. V segue a guarda de abordagem de `conceito.md`.
- "Pegar a versao antiga e trabalhar em cima": mesma metrica, mesmo som, nada alem.
