# 14 — Harmonia Popular: Cifras e Acordes Estendidos

**Referências:** Open Music Theory, capítulos sobre harmonia popular/jazz
e cifras (lead sheets) (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Em música popular e jazz, acordes costumam ser escritos como cifras
(lead sheet chord symbols: `Dm7`, `G7`, `Cmaj7`...) em vez de partitura
completa. A progressão `ii7-V7-IMaj7` (a cadência ii-V-I, ou "two-five-one")
é a progressão cadencial mais comum do jazz — a mesma lógica funcional dos
numerais romanos que você já viu no módulo 06, só que com acordes de sétima
em vez de tríades. Em Dó maior, isso significa ii7 = Ré menor com sétima
(Dm7), V7 = Sol com sétima (G7), IMaj7 = Dó com sétima maior (Cmaj7) — e
as versões com nona ficam Dm9, G9 e Cmaj9. Acordes estendidos (9ª, 11ª,
13ª) empilham mais terças acima da sétima, adicionando cor harmônica sem
mudar a função do acorde: um `ii9` ainda funciona como `ii`, só soa mais rico.

## O que o script faz

`build_events()` usa `generate_progression` (já existente) com as
figuras de sétima e nona do music21 (`"ii7"`, `"V7"`, `"IMaj7"`, `"ii9"`,
`"V9"`, `"IM9"`) para tocar a progressão ii-V-I duas vezes: primeiro com
sétimas, depois (após uma pausa) com nonas.

## O que esperar no piano roll

Dois grupos de três blocos de acordes. No primeiro grupo cada acorde tem
4 notas (sétimas); no segundo, cada acorde tem 5 notas (a nona
adicionada) — mesma harmonia, mais denso.
