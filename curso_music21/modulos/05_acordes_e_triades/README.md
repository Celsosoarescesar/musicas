# 05 — Acordes e Tríades

**Referências:** music21 User's Guide, caps. 7, 9 ("Chords"; "Chordify") ·
Open Music Theory, capítulo "Triads and Seventh Chords"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma tríade é um acorde de três notas empilhadas em terças. As quatro
qualidades básicas (maior, menor, diminuta, aumentada) usam a mesma
fundamental mas intervalos internos diferentes, o que muda completamente
o caráter do acorde.

## O que o script faz

`build_events()` toca, em sequência, as tríades maior, menor, diminuta e
aumentada sobre a mesma fundamental (Dó), usando `generate_chord` (já
existente) e `write_events_to_track` para tocar as três notas de cada
acorde simultaneamente.

## O que esperar no piano roll

Quatro blocos de três notas empilhadas, um após o outro, todos começando
na mesma nota (Dó) mas com as outras duas notas em posições ligeiramente
diferentes a cada bloco.
