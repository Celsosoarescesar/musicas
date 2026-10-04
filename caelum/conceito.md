# Caelum -- conceito do album 1

**Fonte da verdade do conceito:** `docs/superpowers/specs/2026-10-04-caelum-album-vida-real-design.md`
(a vida real do autor, o mapa faixa -> parte da vida -> sentimento e as regras de escrita).
Estrutura e plano sonoro: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md`
(as cenas desta spec e a de `2026-10-03-caelum-album-realismo-design.md` foram substituidas pela vida real).
Como usar as pastas: `caelum/README.md`.

## Conceito

**Caelum** (latim: "ceu") e o autor em primeira pessoa, aos 45 anos. O album conta a
historia real dele: a solidao, o trabalho repetitivo, o casamento que acabou, a faculdade
abandonada e o sentir-se incapaz (e a volta: terminou, fez 2 pos-graduacoes e varios cursos), a depressao da pandemia, os anos sem amor, a banda que
nao deu certo e o sonho de viver de musica. **Cada faixa guarda um sentimento ligado a uma
parte dessa historia.** O ceu e a esperanca: apesar de tudo, ainda ha um lugar melhor, e a
alegria de hoje e criar este album.

Regras em todas as faixas:

1. **Um sentimento e uma imagem por faixa**, em primeira pessoa, sem vilao e sem narrador.
2. **Verdade primeiro:** so fatos que o autor deu (spec da vida real); nada inventado alem disso.
3. **Guarda de abordagem:** sem nomes nem detalhes que identifiquem pessoas reais (ex-esposa,
   familia, colegas, empresa). A depressao (05) nomeia o vazio sem romantizar nem sugerir
   autolesao; a esterilidade (03) e tratada com respeito, sem culpar ninguem.

**Final (album 1):** a esperanca. A faixa 10 volta a highway da 01, agora olhando para o ceu.

Genero: nu metal, vocal limpo + grito, sem rap, uma voz so (Caelum, primeira pessoa).

## Arco e faixas

Letras prontas: 01 "Sozinho", 02 "Rotina", 03 (a refazer: fim do casamento), 04 "Barulho" (a ajustar).
Os nomes das pastas seguem os titulos de trabalho (renomeadas em 2026-10-04). Os titulos podem mudar:
escolhidos com o autor, uma faixa por vez.

| Ato | # | Pasta | Parte da vida | Sentimento |
|---|---|---|---|---|
| Isolamento | 01 | `01_sozinho` ("Sozinho") | Sem amigos, vida na solidao | Solidao |
| | 02 | `02_rotina` ("Rotina") | Moto para um trabalho chato e repetitivo, todo dia | Tedio, piloto automatico |
| | 03 | `03_o_que_nao_veio` (a refazer) | Fim do casamento de 10+ anos; esterilidade | Luto pelo que nao veio |
| Queda | 04 | `04_barulho` | Faculdade abandonada, 8+ anos sem estudar... e a volta: terminou a faculdade, 2 pos-graduacoes e varios cursos | Superar as dificuldades: subir uma montanha; "eu nao morro aqui, eu vou subir" (pegada Three Days Grace) |
| | 05 | `05_vazio` | Pandemia em casa, depressao | Vazio e peso: como se a pessoa estivesse se afogando; gancho "me puxa, me puxa" (pedido de socorro) |
| | 06 | `06_tempo_perdido` | Anos perdidos aos 45; "por que eu fiz aquilo? por que nao fiz melhor?" (hoje e fruto das escolhas do passado) | Raiva de si e do tempo perdido |
| Procura | 07 | `07_alguem_ai` | Anos sem amor; busca de quem o compreenda | Desejo de ser entendido |
| Recomeco | 08 | `08_recomeco` | Criar musica hoje | Alegria, recomeco (centro do album) |
| | 09 | `09_tarde_demais` | Banda que nao deu certo; sonho de ser cantor | Medo de ser tarde demais |
| | 10 | `10_caelum` ("Caelum") | Esperanca | O ceu, esperanca |

A 08 e o centro do album: o refrao dela e o mais luminoso e importante.

## Estrutura por faixa (cada musica com a sua forma)

As faixas nao devem seguir a mesma formula (verso, pre-refrao, refrao, ponte). A forma de cada uma
acompanha o sentimento. Tags aceitas pelo ACE-Step (docs oficiais, Tutorial e Musician's Guide):
`[Intro]`, `[Verse]`, `[Pre-Chorus]`, `[Chorus]`, `[Bridge]`, `[Outro]`, `[Build]`, `[Breakdown]`,
`[Drop]` (eletronico), `[Instrumental]`, `[Guitar Solo]`, `[Piano Interlude]`, `[Fade Out]`, `[Silence]`;
descritores como `[Chorus - anthemic]`; vozes de apoio entre parenteses. Nao empilhar muitos
modificadores; a letra e o `prompt` do `faixa.toml` nao podem se contradizer (se a letra pede piano,
o prompt cita piano). As tags sao um pedido, nao garantia: conferir na geracao.

Alavancas para variar: ordem e presenca das secoes; secoes instrumentais; dinamica (build/breakdown);
o final (fade, silencio, corte seco); o tamanho da letra (duracao automatica: menos letra = mais espaco).

| # | Estrutura | Por que |
|---|---|---|
| 01 | Classica: intro, verso, pre, refrao, verso, pre, refrao, ponte, refrao final (feita) | Base do album |
| 02 | Refrao primeiro, sem pre-refrao, breakdown (feita) | Comeca pelo gancho |
| 03 | Intro de riff, verso, verso, refrao tardio, solo de guitarra, ponte, refrao final | Metal melodico mais rapido (Three Days Grace); o refrao so chega depois de dois versos |
| 04 | Sem ponte: versos que encolhem (4, 3, 2 linhas), refrao que cresce (curto, inteiro, gritado em coro), build, breakdown sussurrado (contagem de degraus), resposta falada (o ceu visto de cima), grito curto "eu cheguei" e final seco | A montanha... e ele sobe |
| 05 | Intro longo, verso, riff instrumental pesado, verso, refrao, breakdown, riff, refrao curto, fade out | Pouca letra e peso arrastado |
| 06 | Comeca direto no verso (sem intro nem pre), refrao curto, breakdown, ponte gritada, dois refroes, corte seco | O tempo acaba de repente |
| 07 | Verso esparso, pre, refrao pequeno, verso, pre, build, refrao enorme com coro, final cantado em coro | O hino cresce ate a multidao |
| 08 | Guitarra limpa sozinha, entrada gradual, refrao cedo, solo melodico, refrao final | Alegria; o solo e a comemoracao |
| 09 | Verso falado, refrao, verso falado, silencio, ponte, refrao gritado | A duvida fala e o refrao responde |
| 10 | Espelho da 01 (mesmo intro de highway), refrao final, volta ao intro com piano | Fecha o circulo |

## Plano sonoro

Subir por quintas (mais sustenidos) soa como tensao e afastamento de casa;
descer por quartas, como assentar e voltar. O album se afasta ao maximo do
D menor da 01 (na 06, C# menor) e volta a ele na 10.

| # | Tom | BPM | Peso | Voz |
|---|---|---|---|---|
| 01 | D menor | 100 | Medio | Verso contido, refrao limpo, ponte gritada |
| 02 | A menor | 96 | Medio | Verso falado, refrao limpo, grito curto; groove "marcha" |
| 03 | E menor | 112 | Medio | Verso contido, refrao anthemico (pegada Three Days Grace), sem grito |
| 04 | B menor | 108 | Pesado | Refrao alterna limpo e grito; riff sincopado |
| 05 | F# menor | 92 | Muito pesado | Limpo e grito alternados; a mais suja (a dor do amor) |
| 06 | C# menor | 120 | O mais rapido | Gang vocals, grito forte; breakdown (raiva publica) |
| 07 | F# menor | 112 | Pesado, anthem | Coro (o autor empilhado), refrao grande |
| 08 | B menor | 98 | Medio | Refrao limpo e luminoso, o mais importante |
| 09 | E menor | 104 | Medio | Verso falado, refrao limpo, grito curto |
| 10 | D menor | 100 | Medio a pesado | Refrao gigante, grito final; volta ao tom/BPM da 01 |

Valores sao pontos de partida; ajuste de ouvido na geracao.

### Escalas

- **Menor natural:** base dos riffs de todas as faixas.
- **Menor harmonica (7a elevada):** tensao e aperto (pre-refrao e ponte das faixas mais contidas).
- **Menor melodica (6a e 7a elevadas, subindo):** melodias de refrao do ato final e o refrao da 07 (decisao do usuario); esperanca.

O ACE-Step so recebe o tom (`keyscale`) e nao distingue harmonica de
melodica; isso fica na melodia que voce grava e na camada REAPER.

### Motivos

- **A highway:** abre o album na 01 (sozinho, banco vazio) e volta na 10 (olhando para cima, com destino).
- **O ceu ("caelum"):** a esperanca; aparece mais perto do fim.
- **Voz de dentro:** na 04 ("a voz sou eu") e na 09 (a duvida do "tarde demais").
- **Curva do grito:** nenhum na 03, maximo nas 05 e 06, contido nas 08-10 (a 08 e luminosa).
- **Breakdown** nas faixas 04, 06 e 07.
- **Prompt-base comum:** os dez prompts compartilham a base "2000s nu
  metal, downtuned 7-string guitars, ..., no rap" (sem "melodic": a palavra puxa para metal melodico); cada faixa varia so BPM,
  tom, peso e textura.
- **Linguagem do genero:** frases curtas e diretas, confessionais; ganchos
  repetidos; contraste verso falado, refrao aberto, grito na ponte.

## Producao hibrida

**Camada 1 -- ACE-Step (Kaggle):** banda (bateria, baixo, guitarras de 7
cordas), estrutura, groove, peso do refrao e vocal guia; Demucs separa os
stems.

**Camada 2 -- REAPER:** texturas e transicoes
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
| 01 | Textura de estrada e ruido de vento ao fundo [manual]; reverb na voz [MCP] |
| 02 | Textura seca e ritmada, pulso de motor/eletronico [manual] |
| 03 | Reverb/delay na voz [MCP]; doble no refrao [MCP] |
| 04 | Breakdown: corte/repeticao de trecho [manual] |
| 05 | Saturacao extra no baixo e na voz [MCP: FX] |
| 06 | Breakdown seco antes do refrao final [manual]; gang vocals dobrados [MCP; alinhar/posicionar: manual] |
| 07 | Coro de vozes empilhadas no refrao [MCP: faixas + pan] |
| 08 | Camada de voz melodica e brilho no refrao [MCP + manual] |
| 09 | Texturas eletronicas frias / glitches [manual] |
| 10 | Camada final de coro; master [MCP: apply_master_chain; alinhar/posicionar: manual] |
