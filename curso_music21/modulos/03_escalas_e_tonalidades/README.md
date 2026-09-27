# 03 — Escalas e Tonalidades

**Referências:** `reaper_bridge.midi.generate_scale` (já existente) · Open
Music Theory, capítulo "Major and Minor Scales"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma tonalidade (key) é organizada em torno de uma escala. Dó maior e Lá
menor natural são **relativas**: usam exatamente as mesmas sete notas,
mas soam diferente porque começam (e resolvem) em graus diferentes.

## O que o script faz

`build_pitches()` toca a escala de Dó maior completa e, em seguida, a
escala de Lá menor natural completa, usando `generate_scale` (já usado
pelo MCP server do reaper-copilot).

## O que esperar no piano roll

Duas subidas de escala consecutivas, cobrindo as mesmas sete posições
verticais (mesmas notas), começando em pontos diferentes.
