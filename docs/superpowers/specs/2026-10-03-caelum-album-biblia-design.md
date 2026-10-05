# Caelum -- biblia do album (frente 2) (design)

> **SUBSTITUIDO em 2026-10-04** pelo conceito da vida real: `2026-10-04-caelum-album-vida-real-design.md`. As cenas e os eixos abaixo (pastor, politicos, "monstros", mantra da obediencia) nao valem mais; a estrutura tecnica (tons, bpm, pesos) continua valendo. **Reativado em 2026-10-05 como o arco das faixas M (o livro de Caelum):** ver `2026-10-05-caelum-album-livro-e-vida-design.md` e `caelum/livro.md`; as cenas e os eixos daqui valem so para as pastas `mNN_*`.

Continua `2026-10-02-caelum-album-design.md` (frente 1: piloto). Esta spec
cobre a **frente 2: a biblia do album** -- o arco das 10 faixas, o plano
sonoro, a divisao de trabalho entre ACE-Step e REAPER e as pastas prontas
para a producao. Nao escreve as letras das faixas 02-10 nem produz audio.

## Conceito central

**Caelum e um executor da Ordem Grave.** O executor medieval cumpria
ordens sem questionar; Caelum e a analogia de quem vive dentro de um
sistema fazendo o que mandam sem perguntar por que. O album conta o dia
em que ele pergunta, o que isso custa e a vida que escolhe depois: sair
do sistema e viver como acredita ser o certo, sendo julgado por quem
ainda vive dentro dele.

Dois eixos atravessam todas as faixas:

1. **Obediencia sem questionar** (o executor).
2. **Quem e o monstro.** O sistema chama de "monstro" quem esta fora dele
   (as criaturas que a Ordem fabrica e, no fim, o proprio Caelum). A
   virada: **os verdadeiros monstros sao quem controla o sistema**. Eles
   aparecem nas letras como "voces"/"eles", sem rosto fixo.

**Final (album 1): caminho do meio.** A Ordem continua de pe; Caelum vive
livre fora dela, ao lado dos monstros que ela criou, e aceita ser
julgado. A historia segue num **album 2** (vida fora do sistema), fora do
escopo desta spec.

Herdado da ideia antiga (`music-main/`, a ser removido pelo usuario):
so o conceito (Ordem Grave, monstros criados com alquimia, quebra de fe,
investigacao). Genero, vozes, faixas, prompts e fluxo sao os do album
Caelum (nu metal melodico, vocal limpo + grito, sem rap, uma voz so em
primeira pessoa, sem narrador).

## Arco e faixas

Tres atos. As faixas 02-03 sao *flashback* (a 01 abre pelo ponto de
virada); a ordem do disco e a da tabela.

| Ato | # | Slug | Titulo | Cena de Caelum | "Monstro" quer dizer |
|---|---|---|---|---|---|
| Fe | 01 | `01_quebra_de_fe` | Quebra de fe (**pronta**) | Descobre que a Ordem cria os monstros que ele executava | Os monstros eram obra da Ordem |
| | 02 | `02_executor` | Executor | Orgulho de cumprir ordens; a primeira duvida | Monstro = o que a Ordem manda executar |
| | 03 | `03_silencio` | Silencio | Ignora os sinais para nao perder a fe | O silencio dele alimenta o sistema |
| Ruptura | 04 | `04_a_mao_que_me_fez` | A mao que me fez | Raiva contra a Ordem que o formou | A mao que cria e a que merece o nome |
| | 05 | `05_culpa` | Culpa | Cada monstro que executou tinha um rosto | Os "monstros" tinham rosto |
| | 06 | `06_revolta` | Revolta | Rompe com a Ordem | Ele ja e chamado de monstro |
| | 07 | `07_do_outro_lado` | Do outro lado | Decide lutar contra a Ordem e se alia aos monstros | Escolhe ficar com os chamados monstros |
| Nova realidade | 08 | `08_monstros` | Monstros | Ve o mundo pelos olhos dos monstros, nao mais da Ordem | **Virada:** o rotulo se inverte; o monstro e quem controla o sistema |
| | 09 | `09_fora_do_sistema` | Fora do sistema | E discriminado e julgado por quem vive dentro dele | Quem esta dentro o chama de monstro; ele sabe quem e |
| | 10 | `10_caelum` | Caelum | Faixa-titulo: quem se tornou, vivendo como pessoa alternativa fora do sistema, julgado | Assume o rotulo sem aceitar o significado |

A faixa 08 e o centro do album: seu refrao e o mais importante para a
inversao do "monstro".

## Plano sonoro

### Tons (circulo das quintas) e BPM

Subir por quintas (mais sustenidos) soa como tensao e afastamento de
casa; descer por quartas, como assentar e voltar. O album se afasta o
maximo possivel do tom da faixa 01 e volta a ele. D menor na 01 e o tom do
sistema; na 10 e o tom do proprio Caelum.

| Ato | # | Tom | BPM | Peso | Voz |
|---|---|---|---|---|---|
| Fe | 01 | D menor | 100 | Medio | Verso contido, refrao limpo, ponte gritada (pronta) |
| | 02 | A menor | 96 | Medio | Verso falado, refrao limpo, grito curto; groove "marcha", caixa seca |
| | 03 | E menor | 88 | Leve | Sussurro e limpo, **sem grito**; a mais contida |
| Ruptura | 04 | B menor | 108 | Pesado | Refrao alterna limpo e grito; riff sincopado |
| | 05 | F# menor | 92 | Muito pesado, arrastado | Limpo e grito alternados; a mais "suja" |
| | 06 | C# menor (**ponto mais distante**) | 120 | O mais rapido | Gang vocals, grito forte; breakdown antes do refrao final |
| Nova realidade | 07 | F# menor | 112 | Pesado, anthem | Coro (os monstros), refrao grande e cantavel |
| | 08 | B menor | 98 | Medio | Refrao limpo, o mais importante; mantra invertido |
| | 09 | E menor | 104 | Medio | Verso falado, refrao limpo, grito curto; eletronica fria |
| | 10 | D menor | 100 | Medio a pesado | Refrao limpo gigante, grito final; **volta ao tom e BPM da 01** |

Os valores sao pontos de partida; o usuario ajusta de ouvido na geracao.
Todos os tons ficam numa tessitura cantavel pelo usuario com D menor como
centro.

### Escalas (natural, harmonica, melodica)

| Escala | Som | Uso |
|---|---|---|
| Menor natural | Estavel, escura | Base dos riffs de todas as faixas |
| Menor harmonica (7a elevada) | Tensa, ritual, "oficial" | A voz da Ordem: mantra, pre-refrao e ponte nas faixas 01-03 |
| Menor melodica (6a e 7a elevadas, subindo) | Aberta, ascendente | Melodias de refrao do ato 3 e o refrao da 07 (uniao com os monstros); sensacao de saida e esperanca; mantra invertido |

**Limite do ACE-Step:** o campo `keyscale` aceita tom (ex.: "D minor") e
nao distingue harmonica de melodica; isso so entra como sugestao no texto
do prompt, sem garantia. A escala "de verdade" vem da melodia que o
usuario grava e da camada REAPER. O ACE-Step recebe so o tom.

### Motivos e curvas do album

- **Mantra da Ordem** ("Obey. Don't ask."): sussurrado/monotono nas faixas
  01-03; **invertido** ("Ask. Don't obey.") nas 08-10. Gravado com a voz do
  usuario na camada REAPER, nao gerado pelo ACE-Step.
- **Curva do grito:** nenhum na 03; maximo nas 05 e 06; volta contido nas
  08-10, como decisao e nao so raiva.
- **Breakdown** nas faixas 04, 06 e 07 (do arranjo do ACE-Step ou de
  edicao no REAPER).
- **Prompt-base comum** a todas as faixas ("melodic nu metal, downtuned
  7-string guitars, ..., no rap"); cada faixa varia so BPM, tom, peso e
  textura, para o album soar como um disco so.
- **Linguagem do genero na letra:** frases curtas e diretas, confessionais;
  ganchos repetidos que viram mantra; contraste verso falado/sussurrado,
  refrao aberto, grito na ponte.

## Producao hibrida em duas camadas

**Camada 1 -- ACE-Step (Kaggle):** a banda (bateria, baixo, guitarras de 7
cordas), a estrutura (verso/refrao/ponte), o groove sincopado, o peso do
refrao e o vocal guia; Demucs separa os stems (fluxo da frente 1).

**Camada 2 -- REAPER:** o que o ACE-Step faz mal ou de forma incerta:
mantra da Ordem (voz do usuario com efeito), texturas e transicoes
(glitches, risers, pads frios, impactos), scratches/samples (se o usuario
tiver ou gravar), tratamento da voz (grito, dobros, efeitos por ato) e
edicoes (cortar/empilhar/repetir para breakdown e ganchos).

**Capacidades do `reaper_bridge`.** Ja existem (verificadas): volume, pan,
FX, importar audio, aplicar master, renderizar, montar sessao vocal. **Nao
verificadas ao vivo** (so entram quando uma faixa precisar, e cada uma e
confirmada ao vivo em faixas temporarias novas, como no montador de
sessao): posicionar itens na linha do tempo, envelopes, recortar/dividir
itens, criar samples. Sao escritas pelo repositorio a partir da API
publica do REAPER; **nao** se recria o ReaAssist (Lua, licenca "all rights
reserved", sem redistribuicao nem obra derivada; alem disso e so uma janela
de chat dentro do REAPER, sem interface externa, e exige chave de API paga,
nao a assinatura do Claude Code). O usuario pode instalar e usar o
ReaAssist por conta propria, sem ligacao com o repositorio.

## Entregaveis

1. **`caelum/BIBLIA.md`** -- conceito, os dois eixos, arco, plano sonoro
   (tons, escalas, BPM, peso, voz), motivos, producao hibrida e uma ficha
   por faixa: cena, o que "monstro" quer dizer ali, voz, tom/escala/BPM,
   prompt, camada REAPER (marcando o que o MCP ja faz e o que e manual).
2. **Pastas `caelum/02_<slug>/` ... `caelum/10_<slug>/`**, copiadas de
   `caelum/_modelo/`, cada uma com `faixa.toml` (prompt, BPM, tom, duracao,
   seed, `vocal_language`, `lufs_target`) e `letra_pt.md` com o contexto da
   cena preenchido e a letra em branco. `letra_en.md` e `pronuncia.md`
   ficam como no modelo, para serem feitos na producao de cada faixa. A
   pasta da 01 ja existe e so e conferida contra a biblia.
3. **Protecao no `caelum.faixa`/`gerar`:** `letra_en.md` ainda com o texto
   de modelo (placeholders) deve falhar antes de criar a musica no banco ou
   falar com o Kaggle, para nao gastar uma geracao com a letra de modelo.
4. Ajuste da 01: a letra e a pronuncia ja foram corrigidas (executor, nao
   cacador) em 2026-10-03; a biblia so registra isso.

## Testes e criterios de sucesso

- Testes automatizados: `load_faixa` carrega as 10 pastas (a 01 completa;
  02-10 so validas ate a `letra_en.md`), a protecao contra letra de modelo
  e a regra de BPM/tom coerente com a biblia (cada `faixa.toml` bate com a
  tabela). Suite completa verde, com REAPER mockado.
- O usuario le a biblia e confirma: (a) o arco conta a historia que ele
  imagina; (b) a inversao do "monstro" esta clara e chega na 08; (c) o plano
  sonoro soa coerente e cantavel; (d) a divisao ACE-Step/REAPER faz sentido.

## Fora do escopo

Letras completas das faixas 02-10, geracao de audio, gravacao, mix e
master, divulgacao, o album 2, a implementacao das capacidades REAPER
nao verificadas (so a lista delas), qualquer app/front-end novo.

## Riscos

- O ACE-Step nao respeita BPM/tom/peso pedidos de forma exata; mitigacao: o
  piloto mostrou que o prompt funciona, e cada faixa tem tentativas
  (seeds).
- Letra de modelo enviada ao Kaggle por engano -- coberta pela protecao do
  item 3.
- Plano de escalas depende da voz do usuario e da camada REAPER, nao do
  ACE-Step (ver limite acima).
