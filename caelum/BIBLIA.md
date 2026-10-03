# Caelum -- biblia do album 1

Specs: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md` (estrutura, plano sonoro)
e `docs/superpowers/specs/2026-10-03-caelum-album-realismo-design.md` (conceito real, que
substitui as cenas da spec anterior). Como usar as pastas: `caelum/README.md`.

## Conceito

**Caelum** (latim: "ceu") e o autor em primeira pessoa: cresceu olhando para
cima, dentro de um sistema de fe e poder, obedeceu sem perguntar, descobriu
como esse sistema usa as pessoas, saiu e vive do seu jeito, julgado por quem
ainda esta dentro. A historia parte da vivencia do usuario (falsos pastores,
politicos, relacionamentos); as faixas misturam confissao direta e
personagem, sem nomear pessoas, igrejas ou partidos reais.

Eixos em todas as faixas:

1. **Obediencia sem questionar:** o membro que faz o que mandam.
2. **Quem e o monstro.** O sistema chama de "perdido", "rebelde" ou "inimigo"
   quem acorda. A virada: os verdadeiros monstros sao quem manipula (o pastor
   que vive do sofrimento dos outros, o politico que rouba a nacao, quem
   mente no amor), nao quem acorda. Quem julga Caelum tambem e vitima do
   mesmo controle. Aparecem nas letras como "voces"/"eles", sem rosto fixo.
3. **Varias formas de ser enganado:** por lideres de fe, por politicos, por
   quem se ama.

**Guarda de abordagem:** a critica e ao **mecanismo de controle** (quem
manipula e lucra com fe, medo, culpa e esperanca), nao as pessoas que
acreditam. Figuras genericas, sem nomes reais. O mesmo vale para pessoas privadas
(ex-parceiro, familia, conhecidos): nada que as identifique.

**Final (album 1): caminho do meio.** O sistema continua; Caelum vive livre
fora dele e aceita ser julgado. A historia segue num album 2.

Genero: nu metal melodico, vocal limpo + grito, sem rap, uma voz so (Caelum,
primeira pessoa), sem narrador.

## Arco e faixas

As faixas 02-03 sao flashback (a 01 abre pelo ponto de virada). As letras
das faixas 01 e 02 foram refeitas no conceito real (2026-10-03). A varredura
de vocabulario dos testes vale para todas as pastas (a lista de isencao
`PENDING_REWRITE` em `tests/test_caelum_biblia.py` esta vazia).

| Ato | # | Pasta | Cena | "Monstro" quer dizer |
|---|---|---|---|---|
| Fe | 01 | `01_quebra_de_fe` (pronta; letra no conceito real) | Descobre que o pastor em quem confiava vive do sofrimento dos outros | O pastor que lucra com a fe |
| | 02 | `02_obedecer` | Crescer fazendo o que mandam, sem perguntar | Quem manda sem dar razao |
| | 03 | `03_silencio` | Ama quem nao o ama de volta e cala para nao perder a amizade | Nao ha monstro: o silencio pesa mais que um nao |
| Ruptura | 04 | `04_pastor` | Raiva do falso pastor que lucra com a dor | Quem vive do sofrimento alheio |
| | 05 | `05_veneno` | O amor que nao deu certo: enganado por quem dizia amar | Quem usa o amor como arma |
| | 06 | `06_promessas` | Politicos que roubam a nacao; a promessa vendida ao povo | Quem rouba e promete |
| | 07 | `07_do_outro_lado` | Percebe que nao esta sozinho: muita gente enganada e julgada | Os rotulados sao os enganados |
| Nova realidade | 08 | `08_monstros` | O monstro nao e quem acorda, e quem manipula | **Virada:** quem controla o sistema |
| | 09 | `09_fora_do_sistema` | E julgado por quem ainda vive dentro dele | Quem esta dentro o chama de monstro |
| | 10 | `10_caelum` | Faixa-titulo: quem se tornou, julgado e assumido | Assume o rotulo sem aceitar o significado |

A 08 e o centro do album: o refrao dela e o mais importante para a inversao
do "monstro".

## Plano sonoro

Subir por quintas (mais sustenidos) soa como tensao e afastamento de casa;
descer por quartas, como assentar e voltar. O album se afasta ao maximo do
D menor da 01 (na 06, C# menor) e volta a ele na 10.

| # | Tom | BPM | Peso | Voz |
|---|---|---|---|---|
| 01 | D menor | 100 | Medio | Verso contido, refrao limpo, ponte gritada |
| 02 | A menor | 96 | Medio | Verso falado, refrao limpo, grito curto; groove "marcha" |
| 03 | E menor | 88 | Leve | Sussurro e limpo, sem grito |
| 04 | B menor | 108 | Pesado | Refrao alterna limpo e grito; riff sincopado |
| 05 | F# menor | 92 | Muito pesado | Limpo e grito alternados; a mais suja (a dor do amor) |
| 06 | C# menor | 120 | O mais rapido | Gang vocals, grito forte; breakdown (raiva publica) |
| 07 | F# menor | 112 | Pesado, anthem | Coro (os enganados), refrao grande |
| 08 | B menor | 98 | Medio | Refrao limpo, o mais importante; mantra invertido |
| 09 | E menor | 104 | Medio | Verso falado, refrao limpo, grito curto |
| 10 | D menor | 100 | Medio a pesado | Refrao gigante, grito final; volta ao tom/BPM da 01 |

Valores sao pontos de partida; ajuste de ouvido na geracao.

### Escalas

- **Menor natural:** base dos riffs de todas as faixas.
- **Menor harmonica (7a elevada):** a voz do sistema (mantra, pre-refrao e ponte nas faixas 01-03).
- **Menor melodica (6a e 7a elevadas, subindo):** melodias de refrao do ato 3 e o refrao da 07 (a uniao dos enganados, decisao do usuario); esperanca; mantra invertido.

O ACE-Step so recebe o tom (`keyscale`) e nao distingue harmonica de
melodica; isso fica na melodia que voce grava e na camada REAPER.

### Motivos

- **Mantra da obediencia:** "Obey. Don't ask." sussurrado/monotono nas
  faixas 01-02 (na 03 vira "Don't ask. Don't hope.", a voz dele mesmo); invertido, "Ask. Don't obey.", nas 08-10. E a voz de qualquer
  sistema que pede obediencia (pulpito, palanque, relacao abusiva). Gravado
  com a sua voz no REAPER.
- **Curva do grito:** nenhum na 03, maximo nas 05 e 06, contido nas 08-10.
- **Breakdown** nas faixas 04, 06 e 07.
- **Prompt-base comum:** os dez prompts compartilham a base "melodic nu
  metal, downtuned 7-string guitars, ..., no rap"; cada faixa varia so BPM,
  tom, peso e textura.
- **Linguagem do genero:** frases curtas e diretas, confessionais; ganchos
  repetidos; contraste verso falado, refrao aberto, grito na ponte.

## Producao hibrida

**Camada 1 -- ACE-Step (Kaggle):** banda (bateria, baixo, guitarras de 7
cordas), estrutura, groove, peso do refrao e vocal guia; Demucs separa os
stems.

**Camada 2 -- REAPER:** mantra da obediencia, texturas e transicoes
(glitches, risers, pads frios, impactos), scratches/samples (se voce tiver ou
gravar), tratamento da voz (grito, dobros, efeitos por ato) e edicoes
(breakdown, ganchos repetidos).

Capacidades do `reaper_bridge`:

- **Ja existem (verificadas):** volume, pan, FX, importar audio, aplicar
  master, renderizar, montar a sessao vocal.
- **Nao verificadas ao vivo (so entram quando uma faixa precisar, sempre
  confirmadas em faixas temporarias novas):** posicionar itens na linha do
  tempo, envelopes, recortar/dividir itens, criar samples. Ate la, sao
  trabalho manual no REAPER.

O ReaAssist (assistente em Lua para o REAPER) nao e recriado aqui: a
licenca e "all rights reserved" (sem redistribuicao nem obra derivada), ele
so funciona como janela de chat dentro do REAPER e exige chave de API paga.
Voce pode instalar e usar por conta propria, sem ligacao com o repositorio.

## Fichas das faixas

Cada pasta `caelum/NN_slug/` tem `faixa.toml` (prompt, BPM, tom) e
`letra_pt.md` com o contexto da cena. `letra_en.md` e `pronuncia.md` das
faixas ainda nao escritas sao feitos na producao de cada uma (o
`caelum_gerar` recusa gerar enquanto a `letra_en.md` for o modelo).

Camada REAPER por faixa ([MCP] = ja da para fazer com as ferramentas
atuais; [manual] = no REAPER, por enquanto):

| # | Camada REAPER |
|---|---|
| 01 | Mantra sussurrado ao fundo do verso [MCP: faixa + FX; posicionar: manual] |
| 02 | Mantra falado, voz de pulpito; textura seca e ritmada [manual] |
| 03 | Mantra "Don't ask. Don't hope." sussurrado, gravado com a sua voz [MCP: faixa + FX; posicionar: manual]; texturas frias e silencios [manual]; reverb/delay na voz [MCP] |
| 04 | Breakdown: corte/repeticao de trecho [manual] |
| 05 | Saturacao extra no baixo e na voz [MCP: FX] |
| 06 | Breakdown seco antes do refrao final [manual]; gang vocals dobrados [MCP; alinhar/posicionar: manual] |
| 07 | Coro de vozes empilhadas no refrao [MCP: faixas + pan] |
| 08 | Mantra invertido "Ask. Don't obey." (sua voz, melodica) [MCP + manual] |
| 09 | Texturas eletronicas frias / glitches [manual] |
| 10 | Mantra invertido + camada final de coro; master [MCP: apply_master_chain; alinhar/posicionar: manual] |
