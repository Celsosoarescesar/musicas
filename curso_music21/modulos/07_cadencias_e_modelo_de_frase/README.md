# 07 — Cadências e Modelo de Frase

**Referências:** Open Music Theory, capítulo "Cadences"
(https://viva.pressbooks.pub/openmusictheory/).

## Teoria

Uma cadência é o ponto de chegada de uma frase musical, e o tipo de
cadência define quanto repouso (ou tensão) ela entrega:

- **Autêntica (V-I)**: o repouso mais completo, a tônica chegando depois
  da dominante.
- **Meia-cadência (I-V)**: termina na dominante, soa "em aberto", pedindo
  continuação.
- **Plagal (IV-I)**: o "amém" dos hinos — menos tensa que a autêntica, mas
  ainda resolve na tônica.
- **Deceptiva (V-vi)**: prepara a resolução na tônica mas desvia para o vi
  grau — uma surpresa.

## O que o script faz

`build_events()` monta as quatro cadências (todas em Dó maior, via
`generate_progression`) e as toca em sequência, com uma pequena pausa
entre cada uma.

## O que esperar no piano roll

Quatro pares de blocos de acordes, com uma lacuna visível entre cada par.
Ouça (ou olhe as notas) e compare o quanto cada par "resolve" de volta
para Dó-Mi-Sol.
