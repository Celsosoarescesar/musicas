# 02 — Ritmo: Durações e Compassos

**Referências:** music21 User's Guide, caps. 3 (cont.), 14, 19, 27
("Time Signatures and Beats"; "Advanced Durations"; "Grace Notes") · Open
Music Theory, capítulos "Duration & Rhythm" e "Meter"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Duração é quanto tempo uma nota soa, medida em figuras (semibreve, mínima,
semínima, colcheia...), cada uma valendo metade da anterior. Isso é
independente da altura da nota — por isso este módulo usa sempre a mesma
nota (Dó4), variando só a duração.

## O que o script faz

`build_events()` gera quatro eventos `(altura, início, duração)` na mesma
altura, cada um com metade da duração do anterior: semibreve (4 tempos),
mínima (2), semínima (1), colcheia (0.5) — a 120 bpm (0.5s por tempo).

## O que esperar no piano roll

Quatro blocos na mesma linha vertical (mesma altura), cada um com metade
da largura do anterior.
