# 10 — Condução de Vozes

**Referências:** Open Music Theory, capítulo "Voice Leading"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Na condução de vozes tradicional, duas vozes não devem se mover em
quintas ou oitavas paralelas — manter a mesma distância "perfeita" entre
elas de um acorde para o outro enfraquece a independência das vozes.
Movimento contrário (as vozes andam em direções opostas) é a forma mais
segura de evitar isso.

## O que o script faz

Duas vozes, em faixas separadas. Cada uma toca duas frases curtas: a
primeira anda em movimento paralelo (quinta paralela entre as vozes), a
segunda faz a mesma ideia mas com movimento contrário. O script usa
`music21.voiceLeading.VoiceLeadingQuartet` para *detectar de verdade* se
há quinta paralela em cada versão, e imprime o resultado.

## O que esperar no piano roll

Duas faixas, quatro notas cada. Compare a "Voz Superior" nas duas
metades: na primeira ela sobe junto com a "Voz Inferior" (mantendo a
mesma distância vertical), na segunda ela desce enquanto a inferior sobe.
