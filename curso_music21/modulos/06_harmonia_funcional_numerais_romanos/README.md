# 06 — Harmonia Funcional (Numerais Romanos)

**Referências:** music21 User's Guide, cap. 23 ("Roman Numeral Analysis") ·
Open Music Theory, capítulo "Roman Numerals"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Numerais romanos descrevem o grau da escala sobre o qual um acorde é
construído, dentro de uma tonalidade: I é o acorde da tônica, IV o da
subdominante, V o da dominante. A progressão I-IV-V-I é o ciclo harmônico
mais básico da música tonal — sai de casa (I), passa por dois pontos de
tensão crescente (IV, V) e volta (I).

## O que o script faz

`build_events()` usa `generate_progression` (já existente em
`reaper_bridge.midi`) para montar os acordes I, IV, V, I em Dó maior, e
toca cada um como um bloco de três notas simultâneas, um atrás do outro.

## O que esperar no piano roll

Quatro blocos de três notas empilhadas, cada bloco com 1 segundo de
duração: Dó-Mi-Sol, depois Fá-Lá-Dó, depois Sol-Si-Ré, e de volta a
Dó-Mi-Sol.
