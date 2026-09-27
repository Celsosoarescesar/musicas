# 01 — Notas e Alturas

**Referências:** music21 User's Guide, caps. 2-3 ("Notes"; "Pitches,
Durations, and Notes again") · Open Music Theory, capítulo "Pitch and
Pitch Class" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma **altura** (pitch) é uma nota específica (ex.: C4 = Dó central). Uma
**classe de nota** (pitch class) ignora a oitava: C2, C3, C4 e C5 são
alturas diferentes, mas todas pertencem à mesma classe "Dó". Em seguida,
notas com nomes diferentes (Dó, Ré, Mi...) na mesma oitava são classes de
nota diferentes.

## O que o script faz

`build_pitches()` gera duas sequências:

1. A nota Dó em quatro oitavas (2 a 5) — mesma classe, alturas diferentes.
2. As sete notas naturais (Dó a Si) na 4ª oitava — classes diferentes.

## O que esperar no piano roll

Na faixa "Curso 01 - Notas e Alturas": quatro notas na mesma posição
vertical relativa (mesma letra, oitavas diferentes, saltando de 12 em 12
semitons), seguidas de sete notas subindo em posições diferentes.
