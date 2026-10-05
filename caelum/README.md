# Caelum -- album de nu metal

Pasta de trabalho do album (21 faixas: as da vida real do autor, um sentimento por faixa, e as do livro de Caelum, em sinfonico; ordem do disco em `livro.md`). Conceito atual do album:
`docs/superpowers/specs/2026-10-05-caelum-album-livro-e-vida-design.md` (as faixas V seguem
`2026-10-04-caelum-album-vida-real-design.md`). Design original:
`docs/superpowers/specs/2026-10-02-caelum-album-design.md`.

Biblia do album (arco das 10 faixas V, plano sonoro, camada REAPER):
`conceito.md` (spec: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md` e `2026-10-03-caelum-album-realismo-design.md`).

## Uma pasta por faixa

As onze pastas `NN_<slug>/` (10 do album + a faixa extra 11) ja existem (ver `conceito.md`; `_modelo/` e so a referencia
do formato). As dez pastas `mNN_<slug>/` do livro de Caelum seguem o mesmo formato (ver `livro.md`). Cada faixa tem:

- `letra_pt.md` -- fonte da verdade (significado e emocao)
- `letra_en.md` -- adaptacao para ingles, enviada INTEIRA ao ACE-Step (sem comentarios)
- `pronuncia.md` -- folha de pronuncia linha a linha
- `faixa.toml` -- prompt de estilo, bpm, tom, seed, duracao (`duration = "auto"`: cada musica fica com o tamanho que a letra pede; ou um numero em segundos)
- `saida/` -- gerado (nao versionado): `songs.db`, `<id>_master.wav`, `<id>_stem_*.wav`

## Fluxo

1. Letra em portugues -> adaptacao para ingles -> folha de pronuncia (com o Claude).
2. Gerar so a musica: `uv run python scripts/caelum_gerar.py 02_rotina` (use `--seed N` para outra tentativa; `--com-stems` separa os stems ja no kernel, mais lento).
   `--instrumental` tambem exige uma `letra_en.md` sem texto de modelo (a checagem roda primeiro): ponha qualquer texto sem placeholder la se so quiser a base instrumental.
   Ouca o `<id>_master.wav`. **So se voce gostou**, separe os stems (Demucs local, na CPU leva alguns minutos): `uv run python scripts/caelum_stems.py 02_rotina <id>`.
3. No REAPER (projeto novo e vazio), com o MCP conectado: `reaper_build_vocal_session` com a pasta `caelum/02_rotina/saida` e o id da musica (precisa dos stems do passo anterior). Cria as faixas dos stems, `guia_ia` (vocal da IA, silenciado, so para referencia) e `voz_caelum` (armada).
4. Escolha a entrada de audio da faixa `voz_caelum` no REAPER (depende da sua interface) e grave.
5. Mix e master (frente 4 da spec).

O vocal da IA (`guia_ia`) serve so de referencia de pronuncia/fraseado.

## Regras da letra em ingles para o ACE-Step

Fonte: docs oficiais do ACE-Step (Musician's Guide e Tutorial). Letras fora disso saem puladas ou misturadas:

- Linhas de **6 a 10 silabas**, com tamanhos parecidos entre versos (+-2). Linha de 13 ou 15 silabas e resumida ou pulada.
- Etiquetas **numeradas e com uma dica curta**: `[Verse 1 - whispered]`, `[Chorus - melodic]`, `[Bridge - whispered]`. Nada de empilhar dicas.
- `[Intro]` e para atmosfera (instrumental, ex.: `[Intro - ambient]`): **nao ponha letra nele**.
- Linha em branco entre seccoes; a dica na etiqueta deve combinar com o `prompt` do `faixa.toml` (sem conflito).
