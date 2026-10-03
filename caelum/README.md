# Caelum -- album de nu metal

Pasta de trabalho do album (10 musicas). Design:
`docs/superpowers/specs/2026-10-02-caelum-album-design.md`.

Biblia do album (arco das 10 faixas, plano sonoro, camada REAPER):
`BIBLIA.md` (spec: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md`).

## Uma pasta por faixa

As dez pastas `NN_<slug>/` ja existem (ver `BIBLIA.md`; `_modelo/` e so a referencia
do formato). Cada faixa tem:

- `letra_pt.md` -- fonte da verdade (significado e emocao)
- `letra_en.md` -- adaptacao para ingles, enviada INTEIRA ao ACE-Step (sem comentarios)
- `pronuncia.md` -- folha de pronuncia linha a linha
- `faixa.toml` -- prompt de estilo, bpm, tom, seed, duracao
- `saida/` -- gerado (nao versionado): `songs.db`, `<id>_master.wav`, `<id>_stem_*.wav`

## Fluxo

1. Letra em portugues -> adaptacao para ingles -> folha de pronuncia (com o Claude).
2. Gerar: `uv run python scripts/caelum_gerar.py 02_executor` (use `--seed N` para outra tentativa).
   `--instrumental` tambem exige uma `letra_en.md` sem texto de modelo (a checagem roda primeiro): ponha qualquer texto sem placeholder la se so quiser a base instrumental.
3. No REAPER (projeto novo e vazio), com o MCP conectado: `reaper_build_vocal_session` com a pasta `caelum/02_executor/saida` e o id da musica. Cria as faixas dos stems, `guia_ia` (vocal da IA, silenciado, so para referencia) e `voz_caelum` (armada).
4. Escolha a entrada de audio da faixa `voz_caelum` no REAPER (depende da sua interface) e grave.
5. Mix e master (frente 4 da spec).

O vocal da IA (`guia_ia`) serve so de referencia de pronuncia/fraseado.
