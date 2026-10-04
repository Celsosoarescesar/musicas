# Caelum -- album de nu metal (design)

> **SUBSTITUIDO em 2026-10-04** pelo conceito da vida real: `2026-10-04-caelum-album-vida-real-design.md`. As cenas e os eixos abaixo (pastor, politicos, "monstros", mantra da obediencia) nao valem mais; a estrutura tecnica (tons, bpm, pesos) continua valendo.

## Contexto e objetivo

Projeto de um album completo de **10 musicas de nu metal melodico**, no
estilo do Chester Bennington (Linkin Park), com referencias de Three Days
Grace, P.O.D., Korn e Slipknot: vocal limpo melodico com explosoes de
grito, **sem rap**. Substitui a ideia antiga ("Ordini Grave", metal
sinfonico com tres vozes e narrador; material de referencia em
`music-main/`, que sera removido do repositorio).

O artista e o personagem sao **Caelum** -- o usuario, cantando em
primeira pessoa. Nome artistico nas redes sociais: Caelum. Sem narrador
e sem outras vozes: Serana, Elysia e o Sacerdote Escrivao (se
aparecerem) existem so dentro das letras, vistos por Caelum.

**Conceito mantido da ideia antiga:** a Ordem Grave, a Igreja que cria
com alquimia os monstros que Caelum cacava, a quebra de fe e a
investigacao. Todo o resto (genero, vozes, lista de capitulos, prompts,
estrategia, workflow) e recriado.

**Entrega do projeto:** o album de 10 musicas com a voz do usuario,
mixado e masterizado por ele, e divulgado por ele como Caelum.

## Fluxo de producao de cada faixa

1. **Letra em portugues** (fonte da verdade do significado e da emocao),
   escrita pelo usuario com ajuda do Claude.
2. **Adaptacao para ingles** -- nao e traducao literal: ingles natural,
   mesmo sentido e emocao, silabas e acentos que cabem na melodia.
   Idioma final em ingles pelo alcance; o usuario nao domina o ingles,
   por isso a etapa 3.
3. **Folha de pronuncia**, linha a linha: pronuncia escrita em
   portugues, silaba tonica, palavras dificeis destacadas (th, "-ed"
   final, r, h, vogais curtas/longas). A letra pode ser ajustada para
   evitar sons que atrapalhem o usuario, quando houver alternativa boa.
4. **ACE-Step gera a faixa completa** (prompt de estilo + letra em
   ingles) no Kaggle, e o **Demucs (`htdemucs_6s`) separa os stems**
   (vocal, bateria, baixo, guitarra, piano, outros).
5. O **vocal guia da IA e guardado** como referencia de pronuncia e
   fraseado, mas **nao entra na mixagem**.
6. O **usuario grava a propria voz** (limpa e gritada) por cima dos
   stems no REAPER.
7. **Mix e master** feitos pelo usuario.

Limite honesto: o Claude orienta a pronuncia por escrito, mas nao ouve
as gravacoes do usuario; a referencia de audio real e o vocal guia do
ACE-Step.

## Decomposicao em frentes

Cada frente tem seu proprio ciclo spec -> plano -> execucao.

1. **Piloto** (esta spec): uma faixa de ponta a ponta.
2. Biblia do album: arco, 10 faixas, letras e prompts.
3. Producao das 10 faixas.
4. Mix e master do album.
5. Divulgacao como Caelum.

Este documento especifica em detalhe so a frente 1 (mais o passo zero).
As frentes 2-5 estao apenas esbocadas acima.

## Estado do repositorio e passo zero

O projeto vive **dentro do repositorio `daw_music_studio`**
(reaper-copilot), que ja tem a geracao via Kaggle (`ace_step/`), a
separacao de stems (Demucs, no kernel e em `reaper_bridge/stems.py`) e
a integracao com o REAPER (`reaper_bridge/`, `mcp_server.py`).

Na `master`, o `ace_step/` ainda e a versao antiga com tunel ngrok, que
ja falhou na separacao de stems por limite mensal de banda do ngrok. A
versao nova, **kernel batch sem ngrok** (spec
`2026-09-26-ace-step-batch-kernel-design.md`, verificada ao vivo em
2026-09-27), esta so na branch `worktree-ace-step-batch-kernel`, **nao
mesclada**.

**Passo zero:** mesclar essa branch na `master` e validar com uma
geracao real curta (geracao + separacao) antes de qualquer outra coisa.
A branch foi criada antes de trabalhos recentes (curso_music21, auditoria
do REAPER, roteamento), entao o merge exige cuidado com conflitos e
rodar a suite de testes completa depois. Nada do restante comeca antes
disso.

## Componentes novos (frente 1)

### 1. Estrutura `caelum/`

Pasta `caelum/` na raiz do repositorio, uma subpasta por faixa
(`caelum/01_<slug>/` ... `caelum/10_<slug>/`), cada uma com:

- `letra_pt.md`, `letra_en.md`, `pronuncia.md`
- `faixa.toml`: prompt de estilo, BPM, tom, seed, duracao, idioma vocal
- saidas geradas (raw, master, stems, projeto do REAPER) -- ignoradas
  pelo git (`.gitignore` ganha as regras de audio/projeto de `caelum/`)

Documentos e letras sao versionados; audio nao.

### 2. Etapa de idioma

Processo, nao codigo: modelos dos tres arquivos de texto mais o trabalho
conversacional descrito no fluxo acima. Sem script de traducao nem de
contagem de silabas (YAGNI); se o piloto mostrar necessidade, entra
depois. `ace_step/lyrics.py` (letra via API do Claude) **nao e usado**:
as letras entram prontas.

### 3. Comando de geracao

`scripts/caelum_gerar.py <faixa>`: le `faixa.toml` e `letra_en.md`,
chama o pipeline existente (`ace_step.orchestrator.run_generation`, o
mesmo de `scripts/criar_musica.py`) e salva tudo **dentro da pasta da
faixa**. Nao reescreve a geracao; so a configura. Mantem a semantica
atual de erros: o pipeline nunca levanta excecao, registra o erro no
banco da faixa; falha de separacao nao apaga a geracao que ja deu
certo.

### 4. Montador de sessao do REAPER

Funcao nova em `reaper_bridge/` e ferramenta MCP
`reaper_build_vocal_session`. Dada a pasta de stems de uma faixa:

- importa cada stem como uma faixa;
- renomeia o stem de vocal para `guia_ia` e o silencia (mute);
- cria a faixa `voz_caelum`, armada para gravacao.

Hoje o `reaper_bridge` nao tem controle de armar faixa (so le o estado
no `audit.py`); isso e codigo novo e depende do comportamento real do
reapy, que **deve ser verificado ao vivo**, em faixas temporarias novas,
sem tocar nas faixas reais do usuario (efeitos colaterais conhecidos de
operacoes como reordenar/deselecionar tudo).

### 5. Mix e master

Usa o que ja existe (`reaper_add_fx`, `reaper_set_fx_param`, volume/pan,
`reaper_apply_master`, `reaper_render`). No piloto so uma mixagem
rapida de teste. A cadeia de voz e o master do album sao a frente 4.

## Piloto: o que valida

Uma faixa real do album percorre o fluxo inteiro. Escolher uma com
**refrao limpo melodico e parte gritada**, para testar os dois estilos.
A cena especifica e escolhida com o usuario no inicio da frente 1 (a
historia das 10 faixas e da frente 2).

Criterios de sucesso, julgados pelo usuario ao ouvir:

1. **O som e nu metal:** em ate 3 ou 4 tentativas (seeds e variacoes de
   prompt), o ACE-Step entrega groove pesado de guitarra afinada baixo,
   refrao melodico e secao gritada. Se nao, ajusta-se o prompt e, se
   preciso, repensa-se o genero antes de investir nas 10 faixas.
2. **A separacao deixa uma base utilizavel:** com o vocal guia
   silenciado, bateria, baixo, guitarras e outros soam bem, sem
   vazamento de vocal que brigue com a voz do usuario.
3. **A letra e cantavel pelo usuario:** com a folha de pronuncia e o
   vocal guia, ele grava a musica inteira em um numero razoavel de
   takes, sem travar sempre nas mesmas palavras.
4. **A sessao do REAPER funciona:** stems em faixas, voz gravada na
   faixa dedicada, mixagem rapida de teste com tudo junto.

Planos B: se o vocal da IA vazar demais nos stems, gerar a base **sem
vocal** (instrumental) e usar um vocal guia separado so como
referencia; se o ACE-Step nao acertar o estilo, ajustar prompt/genero
antes de seguir.

## Testes

- Automatizados, no estilo do repositorio (REAPER e Kaggle mockados via
  `tests/fakes.py`): comando de geracao (leitura do `faixa.toml`, caminho
  de saida na pasta da faixa) e montador de sessao.
- Ao vivo: merge do passo zero (geracao + separacao reais) e montador de
  sessao no REAPER (faixas temporarias novas).
- Ao final da implementacao, suite completa (`uv run pytest`) verde.

## Fora do escopo desta spec

Divulgacao, mix e master finais, biblia do album e as outras 9 faixas,
checagem automatica de pronuncia (por exemplo transcricao do audio
gravado), qualquer app/front-end novo.
