# 12 — Forma Musical

**Referências:** Open Music Theory, capítulo "Form: Phrase, Period,
Sentence" (https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Um período é a unidade de forma mais básica: duas frases relacionadas,
geralmente com material parecido no início, onde a primeira (frase
antecedente) termina numa cadência aberta e a segunda (frase
consequente) termina numa cadência fechada — como uma pergunta seguida
de uma resposta.

## O que o script faz

`build_events()` monta uma frase antecedente (I-IV-V em Dó maior,
terminando em meia-cadência) e, após uma pausa, a frase consequente
(I-IV-V-I, terminando em cadência autêntica) — reaproveitando
`generate_progression`, já usado nos módulos 06, 07 e 09.

## O que esperar no piano roll

Dois grupos de blocos de acordes separados por uma pausa: o primeiro
grupo (3 acordes) termina em Sol-Si-Ré (dominante, em aberto); o segundo
grupo (4 acordes) começa igual mas termina de volta em Dó-Mi-Sol
(tônica, resolvido).
