# 09 — Dominantes Secundárias e Modulação

**Referências:** Open Music Theory, capítulo "Secondary Dominants /
Tonicization" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma dominante secundária "empresta" a dominante de outro grau da escala
por um instante, tonicizando-o — fazendo aquele acorde soar
momentaneamente como se fosse a tônica de outra tonalidade, sem
realmente modular. `V/V` é a dominante do V: em Dó maior, o V é Sol, e a
dominante de Sol é Ré maior. Tocar V/V antes do V de verdade reforça a
chegada na dominante.

## O que o script faz

`build_events()` usa `generate_progression` com a notação `"V/V"` (que o
music21 entende nativamente) para montar I - V/V - V - I em Dó maior.

## O que esperar no piano roll

Quatro blocos de acordes: Dó-Mi-Sol, depois Ré-Fá#-Lá (o V/V — repare no
Fá sustenido, fora da tonalidade de Dó!), depois Sol-Si-Ré, e de volta a
Dó-Mi-Sol.
