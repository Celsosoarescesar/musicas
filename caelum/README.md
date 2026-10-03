# Caelum -- album de nu metal

Pasta de trabalho do album (10 musicas). Design:
`docs/superpowers/specs/2026-10-02-caelum-album-design.md`.

Biblia do album (arco das 10 faixas, plano sonoro, camada REAPER):
`BIBLIA.md` (spec: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md` e `2026-10-03-caelum-album-realismo-design.md`).

## Uma pasta por faixa

As dez pastas `NN_<slug>/` ja existem (ver `BIBLIA.md`; `_modelo/` e so a referencia
do formato). Cada faixa tem:

- `letra_pt.md` -- fonte da verdade (significado e emocao)
- `letra_en.md` -- adaptacao para ingles, enviada INTEIRA ao ACE-Step (sem comentarios)
- `pronuncia.md` -- folha de pronuncia linha a linha
- `faixa.toml` -- prompt de estilo, bpm, tom, seed, duracao (`duration = "auto"`: cada musica fica com o tamanho que a letra pede; ou um numero em segundos)
- `saida/` -- gerado (nao versionado): `songs.db`, `<id>_master.wav`, `<id>_stem_*.wav`

## Fluxo

1. Letra em portugues -> adaptacao para ingles -> folha de pronuncia (com o Claude).
2. Gerar: `uv run python scripts/caelum_gerar.py 02_obedecer` (use `--seed N` para outra tentativa).
   `--instrumental` tambem exige uma `letra_en.md` sem texto de modelo (a checagem roda primeiro): ponha qualquer texto sem placeholder la se so quiser a base instrumental.
3. No REAPER (projeto novo e vazio), com o MCP conectado: `reaper_build_vocal_session` com a pasta `caelum/02_obedecer/saida` e o id da musica. Cria as faixas dos stems, `guia_ia` (vocal da IA, silenciado, so para referencia) e `voz_caelum` (armada).
4. Escolha a entrada de audio da faixa `voz_caelum` no REAPER (depende da sua interface) e grave.
5. Mix e master (frente 4 da spec).

O vocal da IA (`guia_ia`) serve so de referencia de pronuncia/fraseado.

## Regras da letra em ingles para o ACE-Step

Fonte: docs oficiais do ACE-Step (Musician's Guide e Tutorial). Letras fora disso saem puladas ou misturadas:

- Linhas de **6 a 10 silabas**, com tamanhos parecidos entre versos (+-2). Linha de 13 ou 15 silabas e resumida ou pulada.
- Etiquetas **numeradas e com uma dica curta**: `[Verse 1 - whispered]`, `[Chorus - melodic]`, `[Bridge - whispered]`. Nada de empilhar dicas.
- `[Intro]` e para atmosfera (instrumental, ex.: `[Intro - ambient]`): **nao ponha letra nele**. O mantra e gravado por voce no REAPER.
- Linha em branco entre seccoes; a dica na etiqueta deve combinar com o `prompt` do `faixa.toml` (sem conflito).
