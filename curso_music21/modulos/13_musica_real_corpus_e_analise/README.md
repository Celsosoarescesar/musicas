# 13 — Música Real: Corpus e Análise

**Referências:** music21 User's Guide, caps. 11, 53 ("Corpus Searching";
"Advanced Corpus and Metadata Searching") · corpus de corais de Bach
embutido no music21 (offline, sem acesso à internet).

## Teoria

Até aqui, todo o material foi gerado programaticamente. Este módulo usa
o corpus embutido do music21 — centenas de obras prontas, incluindo
uma quantidade grande de corais a quatro vozes de Bach — para trabalhar
com música real. As quatro vozes (Soprano, Alto, Tenor, Baixo) são
exatamente o tipo de condução de vozes e contraponto estudado nos
módulos 10 e 11, só que escritas por Bach.

## O que o script faz

Carrega o coral BWV 66.6 do corpus (`music21.corpus.parse`), recorta a
primeira frase (dois compassos), escreve cada voz numa faixa separada do
REAPER (`write_score_to_tracks`, agora corrigido para limpar a faixa
antes de reescrever e evitar colisão de nomes entre vozes), detecta a
tonalidade da primeira frase automaticamente (confirmando que toniciza Lá
maior — a relativa maior, antes de o coral inteiro resolver em Fá# menor)
e conta quantas obras de Bach existem no corpus (nem todas são corais a 4
vozes).

## O que esperar no piano roll

Quatro faixas (Soprano, Alto, Tenor, Baixo), cada uma com uma linha
melódica real de Bach, tocando juntas — a primeira frase do coral.
