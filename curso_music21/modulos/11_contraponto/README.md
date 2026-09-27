# 11 — Contraponto

**Referências:** Open Music Theory, capítulo "Species Counterpoint"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Contraponto de primeira espécie: uma nota de contraponto para cada nota
do cantus firmus (a melodia fixa), sempre em intervalos consonantes
(uníssono, 3ª, 5ª, 6ª, 8ª), evitando quintas e oitavas paralelas entre as
duas vozes — a mesma regra do módulo 10, aplicada nota a nota numa
melodia inteira. É a técnica que Bach (e os compositores antes dele)
usavam para escrever vozes independentes que soam bem juntas — o que
volta a aparecer no módulo 13, analisando corais de Bach de verdade.

## O que o script faz

Toca o cantus firmus (Dó-Ré-Mi-Fá-Mi-Ré-Dó) numa faixa e o contraponto
escrito sobre ele em outra. `build_verificacao()` confirma, nota por
nota, que todos os intervalos são consonantes e que não há quinta,
oitava ou uníssono paralelo entre nenhum par de notas consecutivas —
usando o mesmo `music21.voiceLeading.VoiceLeadingQuartet` do módulo 10.

## O que esperar no piano roll

Duas faixas com sete notas cada, tocando juntas. A primeira e a última
nota das duas vozes formam uma oitava (começo e fim tradicionais do
contraponto de primeira espécie).
