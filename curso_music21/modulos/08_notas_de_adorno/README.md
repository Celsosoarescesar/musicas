# 08 — Notas de Adorno

**Referências:** Open Music Theory, capítulo "Embellishing Tones"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Notas de adorno (non-chord tones) são notas de uma melodia que não
pertencem ao acorde tocado naquele momento — passam rápido, preenchendo o
espaço entre as notas do acorde. A mais comum é a nota de passagem:
preenche o intervalo entre duas notas do acorde andando por grau
conjunto (um passo de escala de cada vez).

## O que o script faz

`build_events()` toca primeiro o "esqueleto" — só as notas do acorde de
Dó (Dó-Mi-Sol-Dó) — e depois a mesma linha preenchida com a escala
completa (Dó-Ré-Mi-Fá-Sol-Lá-Si-Dó), onde Ré, Fá, Lá e Si são notas de
passagem entre as notas do acorde.

## O que esperar no piano roll

Quatro notas espaçadas, uma pausa, e depois oito notas mais rápidas
preenchendo o mesmo contorno melódico (sobe de Dó a Dó).
