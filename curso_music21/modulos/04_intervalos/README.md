# 04 — Intervalos

**Referências:** music21 User's Guide, cap. 18 ("Intervals") · Open Music Theory, capítulo "Intervals" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Um intervalo é a distância entre duas notas. `P1` (uníssono, distância zero), `M3` (terça maior), `P5` (quinta justa) e `P8` (oitava) são os intervalos que formam a base da tríade maior e da relação de oitava.

## O que o script faz

`build_pitches()` toca a nota Dó4 (fundamental), e depois cada intervalo (`P1`, `M3`, `P5`, `P8`) aplicado sobre essa mesma fundamental, usando `music21.interval.Interval.transposePitch`.

## O que esperar no piano roll

A mesma nota repetida (fundamental, depois uníssono), seguida de três notas subindo — terça, quinta e oitava acima da fundamental.
