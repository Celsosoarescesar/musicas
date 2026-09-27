# Módulo 15 — Composição e Arranjo Multi-Instrumental (capstone)

## Contexto

Este é o capstone do currículo (`docs/superpowers/specs/2026-09-27-curso-music21-design.md`,
seção "Módulo 15 — detalhamento"): compor uma peça curta original e
arranjá-la em 6 faixas/instrumentos do REAPER, reaproveitando harmonia
(módulos 06/09), condução de vozes (módulo 10), forma (módulo 12) e
motivo/transformação (novo aqui). Este documento detalha as decisões
técnicas concretas — o spec original descreve a intenção; este documento
fixa os dados exatos que o plano de implementação vai transcrever.

## Duas decisões de abordagem (confirmadas com o usuário)

1. **Plugins/instrumentos:** o script **não** chama `reaper_add_fx`. Ele só
   escreve MIDI nas 6 faixas; o README instrui o usuário a adicionar um
   instrumento (VST) apropriado em cada faixa manualmente. Isso evita que
   a lição falhe em máquinas sem os plugins certos instalados — a mesma
   razão pela qual o spec original já dizia "o nome do plugin depende do
   que está instalado".
2. **Técnica composicional:** motivo curto + transformações clássicas
   (transposição, inversão, retrógrado) + forma, em vez de uma melodia
   escrita nota a nota sem estrutura. Reaproveita mais conceitos do curso
   de uma vez (e é o que o spec original já sugeria com "motivo + forma").

## Harmonia

Reaproveita a progressão I-IV-V-I em Dó maior já usada nos módulos 06 e
12 (`[[60,64,67],[65,69,72],[67,71,74],[60,64,67]]`), 2 segundos por
acorde, 8 segundos no total. Não precisa de `generate_progression` de
novo — os valores já estão fixados e verificados desde o módulo 06.

## Motivo e transformações (verificado ao vivo antes deste documento)

Para garantir que toda transformação continue dentro do tom (sem
acidentes cromáticos indesejados), o motivo e suas transformações são
definidos em **graus de escala** (não semitons), convertidos para MIDI
por uma função diatônica pequena:

```python
INTERVALOS_MAIOR = [0, 2, 4, 5, 7, 9, 11]

def grau_para_midi(grau: int, tonica: int = 60) -> int:
    oitava, posicao = divmod(grau, 7)
    return tonica + oitava * 12 + INTERVALOS_MAIOR[posicao]
```

Motivo (graus, relativos à tônica): `[0, 1, 2, 0]` (Dó-Ré-Mi-Dó).

| Transformação | Graus | MIDI | Usada sobre |
|---|---|---|---|
| Motivo original | `[0, 1, 2, 0]` | `[60, 62, 64, 60]` | I |
| Transposição (+3 graus, uma 4ª diatônica) | `[3, 4, 5, 3]` | `[65, 67, 69, 65]` | IV |
| Inversão (nega os graus em torno da tônica) | `[0, -1, -2, 0]` | `[60, 59, 57, 60]` | V |
| Retrógrado (graus invertidos em ordem) | `[0, 2, 1, 0]` | `[60, 64, 62, 60]` | I (final) |

A transposição cai exatamente na fundamental do IV (F4=65) — verificado,
não coincidência do design. O retrógrado termina de volta em Dó4 (60),
fechando a peça na tônica.

Cada célula tem 4 notas de 0.5s, preenchendo os 2.0s de cada acorde —
isso é a faixa **Voz**.

## Os 6 instrumentos e seus papéis (o "como as partes conversam")

Cada instrumento tem uma função rítmica/textural distinta, deliberadamente
diferente das outras, para que a lição possa discutir por que elas não
duplicam a mesma função:

| Faixa | Papel | Conteúdo |
|---|---|---|
| Voz | Melodia principal | motivo + transformações (acima) |
| Piano | Acompanhamento harmônico (comping) | acordes em bloco, 2.0s cada |
| Baixo | Fundação harmônica | só a fundamental de cada acorde, uma oitava abaixo, sustentada 2.0s |
| Bateria | Groove rítmico | kick(36)-hihat(42)-snare(38)-hihat(42), 0.5s cada, repetido a cada acorde — o kick sempre cai exatamente quando o baixo muda de nota, travando o groove com o baixo |
| Guitarra | Contraste rítmico sobre a mesma harmonia | arpejo raiz-3ª-5ª-3ª, 0.5s cada — mais rápido que o piano (blocos) e o baixo (sustentado), a mesma harmonia com uma textura diferente |
| Cordas | Pad de sustentação | só a 3ª e a 5ª de cada acorde (sem a fundamental, para não duplicar demais o baixo/piano), sustentadas 2.0s |

Todos os eventos exatos (pitch, start, duration) para as 6 faixas foram
computados e impressos ao vivo antes deste documento; o plano de
implementação vai transcrever esses valores literalmente.

## Arquitetura

Nenhum código novo no `reaper_bridge`. `main()` faz 6 chamadas de
`lesson_track()` + `write_events_to_track()` (uma por instrumento) dentro
de um único `try`/`except ReaperBridgeError` — o mesmo padrão dos módulos
10 e 11, estendido de 2 para 6 faixas. Cada faixa tem seu próprio
`build_events_<instrumento>()` puro.

Nomes das faixas: `"Curso 15 - Composição e Arranjo (Voz)"`, `"...(Piano)"`,
`"...(Baixo)"`, `"...(Bateria)"`, `"...(Guitarra)"`, `"...(Cordas)"` —
todos distintos entre si e dos módulos 01-14.

## README — conteúdo obrigatório

Além da estrutura padrão (Referências/Teoria/O que o script faz/O que
esperar no piano roll), o README deste módulo precisa de duas seções que
nenhum módulo anterior teve:

1. **"Como as partes conversam"**: discussão explícita de por que cada
   instrumento tem um papel diferente (tabela acima, em prosa), citando
   especificamente como bateria e baixo travam o groove juntos (kick
   alinhado com a troca de nota do baixo) e como a guitarra contrasta
   ritmicamente com o baixo sustentado.
2. **"Prática com voz e teclado MIDI" (opcional)**: instrução em prosa
   apenas — armar uma faixa no REAPER, conectar um teclado MIDI ou
   microfone, gravar (usando a interface nativa do REAPER, sem automação
   nova) uma das partes que o usuário aprendeu a tocar/cantar, comparando
   com a versão gerada por código. Nenhum código novo para isso.

## Testes

Cada `build_events_<instrumento>()` é uma função pura, testada com o
valor literal exato (computado ao vivo antes do plano ser escrito) —
mesmo padrão de todos os módulos anteriores. `main()` não tem teste de
ponta a ponta (depende de REAPER aberto), consistente com o spec geral.

## Ordem de implementação sugerida (2 tarefas)

1. **Núcleo harmônico/melódico**: helper de grau-para-MIDI, `build_events_voz`,
   `build_events_piano`, `build_events_baixo` + testes.
2. **Camada rítmica/textural + integração**: `build_events_bateria`,
   `build_events_guitarra`, `build_events_cordas`, `main()` escrevendo as
   6 faixas, README completo (com as duas seções obrigatórias acima) +
   testes.
