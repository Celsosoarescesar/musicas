# Caelum -- album "o livro e a vida": 21 faixas, duas vozes (2026-10-05)

**Estende** `2026-10-04-caelum-album-vida-real-design.md` (a vida real do autor, que continua
valendo) e **traz de volta** o arco medieval de `2026-10-03-caelum-album-biblia-design.md`
(executor da Ordem Grave), agora como uma historia dentro da outra. Esta e a fonte da verdade
do album a partir de 2026-10-05.

## Ideia (estilo Assassin's Creed)

O autor, hoje, **encontra um livro antigo sobre Caelum**, um executor medieval, e transforma
esse livro em musica. O album tem duas historias que se espelham:

- **V (a vida):** a vida real do autor, com a voz de agora. **Nu metal** melodico (as 10 faixas do
  spec de 2026-10-04). Sem orquestra: cru e pessoal.
- **M (o livro):** a historia de Caelum medieval, do ponto de vista dele, em primeira pessoa e sem
  narrador. **Nu metal sinfonico** (a mesma banda mais orquestra e coral).

Voz sempre a do autor. "Caelum" e o artista, o personagem do livro e o titulo das duas ultimas
faixas; o encontro final das duas historias e proposital.

## Estrutura: 21 faixas = 10 pares V+M, mais Obedecer

Cada faixa V e seguida pela faixa M que espelha o mesmo sentimento no livro. A faixa 11 (Obedecer)
entra antes do Executor. **V e M do mesmo par usam o mesmo tom e o mesmo bpm** (plano de quintas ja
existente), um espelho tambem musical, **exceto nos pares 3 e 7**: ali a V segue o que ja esta no
codigo (V3 E/112 e V7 E/88, esta ultima reaproveita a musica ja gerada) e a M segue o plano da
biblia de 2026-10-03 (M3 E/88, leve e contida; M7 F#/112, hino).

| Par | V: a vida (nu metal) | M: Caelum (sinfonico) | Tom / bpm (V; M) | O espelho |
|---|---|---|---|---|
| 1 | Sozinho | Quebra de fe | D / 100 (igual) | Acha o livro e fica sozinho com uma verdade que ninguem quer ouvir |
| 2 | Rotina, **Obedecer** | Executor | A / 96 | Piloto automatico e obedecer calado <-> cumprir ordens sem perguntar |
| 3 | Nunca foi lar | Silencio | E / 112; E / 88 | A casa que nao foi lar <-> ignorar os sinais para nao perder a fe |
| 4 | Barulho (a montanha) | A mao que me fez | B / 108 | Subir <-> raiva de quem o moldou |
| 5 | Vazio (afogando) | Culpa | F# / 92 | O fundo <-> cada monstro tinha um rosto |
| 6 | Tempo perdido | Revolta | C# / 120 | "Por que obedeci calado?" <-> rompe com a Ordem |
| 7 | Silencio (quem me entenda) | Do outro lado | E / 88; F# / 112 | Ser entendido <-> os monstros que o entendem |
| 8 | Recomeco (o vento) | Monstros | B / 98 | A voz vira onda <-> a virada: o monstro e quem controla o sistema |
| 9 | Tarde demais (as estacoes) | Fora do sistema | E / 104 | O medo do tempo <-> ser julgado por quem ficou |
| 10 | Caelum (passaros e ceu) | Caelum | D / 100 | As duas historias se encontram no ceu |

Ordem do disco: V1, M1, V2 (Rotina), Obedecer, M2, V3, M3, ..., V10, M10 = 21 faixas. Cada par
usa as pastas ja existentes (V) e pastas novas (M); a convencao de nomes das pastas e a ordem de 21 posicoes sao definidas no plano.
Obedecer e a faixa antiga da igreja (A menor, 96 bpm), refeita; ela e V, nao M, e e a unica sem par.

### Historia de Caelum no livro (arco da biblia de 2026-10-03, sem mudancas)

Tres atos. Caelum e executor da Ordem Grave: cumpre ordens sem questionar. Descobre que a Igreja
fabrica os monstros que ele matava, rompe, se junta aos monstros e e julgado.
Final do album 1: caminho do meio (a Ordem continua de pe; Caelum vive livre fora dela). Album 2
(vida fora do sistema) fora do escopo.

Dois eixos: **obediencia sem questionar** e **quem e o monstro** (a virada na M8: os verdadeiros
monstros sao quem controla o sistema; eles aparecem como "voces/eles", sem rosto fixo).

Mantra da Ordem "Obey. Don't ask.": sussurrado nas M1-M3, **invertido** ("Ask. Don't obey.") nas
M8-M10; gravado com a voz do autor na camada REAPER.

## Som

**V:** guitarras de 7 cordas afinadas baixo, verso baixo, refrao limpo, grito quando o sentimento
pede; sem orquestra (plano do spec de 2026-10-04).

**M:** a mesma banda mais orquestra. A orquestra muda de papel por ato:

| Ato | Faixas M | Orquestra | Sensacao |
|---|---|---|---|
| Fe | 1-3 | Orgao, coral grave em canto liturgico, cordas contidas | Som da Ordem: solene, frio, menor harmonica |
| Ruptura | 4-7 | Cordas em tremolo, metais, timpanos contra a distorcao | A orquestra vira ameaca e depois se rompe |
| Nova realidade | 8-10 | Cordas abertas, coral que sobe, menor melodica | O som da Ordem volta transformado em saida e esperanca |

**Pontes entre os mundos:** cada M abre com som de livro (folha, pena na tinta); V abre sem ele.
Na faixa 10, a banda do V e a orquestra do M tocam juntas.

**Escalas:** continuam como sugestao de texto no prompt (o ACE-Step so recebe o tom, nao distingue
harmonica de melodica).

## Fluxo por faixa (inalterado)

1. Cena/imagem combinada com o autor (propor 3-4 imagens com verso de exemplo e recomendacao).
2. Letra PT (poetica, metaforica, uma imagem unica; fonte da verdade). 3. Aprovacao.
4. EN (silabas que cabem na melodia) + pronuncia em PT-BR + `faixa.toml`. 5. Testes.
6. Geracao no ACE-Step (`caelum_gerar`). 7. Stems depois, so se gostar.
8. Autor grava a voz e faz mix/master; merge unico na `main` depois (decisao dele, sem merge antes).

## Regras de escrita

- Primeira pessoa, uma imagem unica por faixa, linhas curtas (ate 10 silabas), sem narrador.
- M: alegoria medieval, sem pessoas, igrejas ou partidos reais; critica o MECANISMO de controle.
- V: sem nomes e sem detalhes que identifiquem pessoas reais; cuidado com depressao (05) e
  esterilidade (03), como no spec de 2026-10-04.
- Pedido de "pegar a versao antiga e trabalhar em cima": mesma metrica, mesmo som, nada alem.

## Piloto e riscos

- **O ACE-Step ainda nao foi testado com orquestra** (cordas fracas, coral artificial). Antes de
  escrever as outras 9 faixas M, gerar so a **M1 Quebra de fe** em 3 ou 4 tentativas (seeds e
  variacoes de prompt). Se o sinfonico nao soar, ajustar o prompt e, se preciso, mover a orquestra
  para a camada REAPER (MIDI e instrumentos virtuais, trabalho manual do autor).
- Trabalho grande: 10 faixas M novas (letra PT/EN, pronuncia, prompt, geracao) mais a Obedecer
  refeita; uma faixa por vez.
- O projeto passa de 10 para 21 pastas em `caelum/`; renomear pastas exige REAPER fechado.

## Fora do escopo desta spec

Letras das faixas M, geracao de audio, gravacao, mix e master, divulgacao, o album 2, e a
renomeacao das pastas existentes (decidida no plano).
