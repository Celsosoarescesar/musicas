# Caelum -- revisao de conceito: do alegorico para o real (design)

Revisa o **conceito e as cenas** de `2026-10-03-caelum-album-biblia-design.md`
(frente 2). O plano sonoro (tons, BPM, curva do grito, escalas, mantra,
producao hibrida) e a estrutura em tres atos NAO mudam. Esta spec troca a
alegoria medieval (Ordem Grave, executor, monstros criados por alquimia) por
**experiencias reais**, e define o que precisa ser refeito.

## Por que mudar

O nu metal (Linkin Park, Korn, Three Days Grace, System of a Down) funciona
por falar de dor, raiva e traicao reais, em primeira pessoa. A fantasia
medieval distancia o ouvinte e enfraquece o grito. O nucleo da historia ja
era real e sobrevive sem a alegoria: obedecer sem questionar, descobrir o
engano, sair, ser rotulado e julgado por quem ficou.

## Conceito (real)

**Caelum** (latim: "ceu") e o autor em primeira pessoa: cresceu olhando
para cima, dentro de um sistema de fe e poder, obedeceu sem perguntar,
descobriu como esse sistema usa as pessoas, saiu e vive do seu jeito,
julgado por quem ainda esta dentro. A historia parte da vivencia do usuario
(falsos pastores, politicos, relacionamentos); as faixas misturam
confissao direta e personagem, sem nomear pessoas, igrejas ou partidos
reais.

Eixos:

1. **Obediencia sem questionar** (era "o executor"; agora e o membro que faz
   o que mandam).
2. **Quem e o monstro.** O sistema chama de "perdido", "rebelde" ou
   "inimigo" quem acorda. A virada: **os verdadeiros monstros sao quem
   manipula** (pastor que vive do sofrimento dos outros, politico que
   rouba a nacao, quem mente no amor), nao quem acorda. Quem julga Caelum
   tambem e vitima do mesmo controle.
3. **Varias formas de ser enganado:** por lideres de fe, por politicos, por
   quem se ama.

**Guarda de abordagem:** a critica e ao **mecanismo de controle** (quem
manipula e lucra com fe, medo, culpa e esperanca), nao as pessoas que
acreditam. Figuras genericas ("o pastor", "o politico", "voces"), sem nomes
reais. Isso mantem a letra mais forte e mais dificil de rebater.

**Final (album 1): caminho do meio.** O sistema continua; Caelum vive livre
fora dele e aceita ser julgado. O album 2 continua dali.

## Arco e faixas

Tons, BPM, peso, voz e escalas por faixa: os mesmos da spec da biblia, por
posicao. Os titulos e cenas mudam:

| Ato | # | Slug (novo) | Titulo | Cena (real) | "Monstro" quer dizer |
|---|---|---|---|---|---|
| Fe | 01 | `01_quebra_de_fe` | Quebra de fe | Descobre que o pastor em quem confiava vive do sofrimento dos outros (a virada; flashback para 02-03) | O pastor que lucra com a fe |
| | 02 | `02_obedecer` | Obedecer | Crescer fazendo o que mandam, sem perguntar | Quem manda sem dar razao |
| | 03 | `03_silencio` | Silencio | Ve os sinais e cala para nao perder o lugar | O silencio alimenta o sistema |
| Ruptura | 04 | `04_pastor` | Pastor | Raiva do falso pastor que lucra com a dor | Quem vive do sofrimento alheio |
| | 05 | `05_veneno` | Veneno | O amor que nao deu certo: enganado por quem dizia amar | Quem usa o amor como arma |
| | 06 | `06_promessas` | Promessas | Politicos que roubam a nacao; a promessa vendida ao povo | Quem rouba e promete |
| | 07 | `07_do_outro_lado` | Do outro lado | Percebe que nao esta sozinho: muita gente enganada e julgada | Os rotulados sao os enganados |
| Nova realidade | 08 | `08_monstros` | Monstros | **Virada:** o monstro nao e quem acorda, e quem manipula | Quem controla o sistema |
| | 09 | `09_fora_do_sistema` | Fora do sistema | E julgado por quem ainda vive dentro dele | Quem esta dentro o chama de monstro |
| | 10 | `10_caelum` | Caelum | Faixa-titulo: quem se tornou, vivendo do seu jeito, julgado e assumido | Assume o rotulo sem aceitar o significado |

A faixa 08 continua sendo o centro do album. Tons/BPM por posicao (nao
mudam): 01 D menor 100; 02 A menor 96; 03 E menor 88; 04 B menor 108; 05 F#
menor 92 (arrastada, a mais suja: combina com a dor do amor); 06 C# menor
120 (a mais rapida: raiva publica); 07 F# menor 112; 08 B menor 98; 09 E
menor 104; 10 D menor 100.

**Mantra:** "Obey. Don't ask." (faixas 01-03) e invertido "Ask. Don't obey."
(08-10) continuam, agora como a voz de qualquer sistema que pede obediencia
(pulpito, palanque, relacao abusiva).

## O que muda no repositorio

1. **Renomear pastas** com `git mv`: `02_executor` -> `02_obedecer`,
   `04_a_mao_que_me_fez` -> `04_pastor`, `05_culpa` -> `05_veneno`,
   `06_revolta` -> `06_promessas`. (01, 03, 07, 08, 09, 10 mantem o slug.)
2. **`letra_pt.md` de 02-10**: contexto da cena no vocabulario real (sem
   Ordem, lamina, alquimia, executor). A letra continua em branco, exceto a
   02, ja escrita (ver 4).
3. **`caelum/BIBLIA.md`, README e testes** (`tests/test_caelum_biblia.py`:
   slugs, `UNWRITTEN`) acompanham a tabela acima; os testes que ja travam
   BPM/tom por posicao seguem valendo.
4. **Letras ja escritas das faixas 01 e 02** (`letra_pt.md`, `letra_en.md`,
   `pronuncia.md`) sao **refeitas com o usuario**, em sessao interativa
   (uma faixa por vez, como no piloto): mesma estrutura e metrica sempre
   que possivel, para a musica gerada (01: Musica #1 aprovada; 02: Musica
   #1 gerada) continuar servindo como base e como vocal guia de melodia.
5. `faixa.toml` de 02-10: os prompts ja sao genericos de estilo (sem
   fantasia); so conferir que nenhum cita elemento alegorico. Nenhum BPM/tom
   muda.
6. **Nao mudam:** o codigo (`caelum/faixa.py`, `gerar`, `vocal_session`), a
   protecao contra letra de modelo, os audios gerados e o projeto do REAPER
   da faixa 01 (`saida/`, nao versionados).

## Criterios de sucesso

- Testes: suite completa verde; `test_caelum_biblia.py` com os novos slugs;
  nenhum arquivo em `caelum/` (fora de `saida/`) cita "Ordem Grave",
  "executor", "alquimia" ou "lamina" como alegoria (um teste de varredura).
- O usuario le a biblia revisada e confirma: (a) a historia e a dele; (b) a
  guarda de abordagem esta respeitada (mecanismo, nao pessoas); (c) cada
  faixa tem uma cena real clara.
- As letras refeitas das faixas 01 e 02 sao aprovadas pelo usuario (fora
  deste plano de arquivos: sao sessoes interativas).

## Fora do escopo

Escrever as letras 03-10 (sessao por faixa, depois), regerar audio das
faixas 01/02 (decisao do usuario depois de ouvir a letra nova), gravar voz,
mix/master, album 2, novas capacidades do `reaper_bridge`.

## Riscos

- Letras reais sobre pessoas e instituicoes podem resvalar para ataque a
  pessoas ou grupos reais; mitigacao: guarda de abordagem acima, revisada
  com o usuario em cada letra.
- A metrica da letra nova pode nao caber na musica ja gerada; mitigacao:
  escrever com a mesma estrutura de silabas e, se nao der, regerar com seed
  nova (custo: ate ~45 min de Kaggle por tentativa).
- Renomear pastas deixa referencias velhas; mitigacao: o teste de varredura
  e os testes de slug da biblia falham se algo ficar para tras.
