# 15 — Composição e Arranjo Multi-Instrumental (Capstone)

**Referências:** todo o curso até aqui, especialmente os módulos 06
(Harmonia Funcional), 09 (Dominantes Secundárias), 10 (Condução de
Vozes), 12 (Forma Musical) — este módulo reaproveita a progressão
I-IV-V-I e o conceito de motivo transformado, aplicando tudo num arranjo
completo.

## Teoria

Compositores clássicos e populares frequentemente constroem uma peça
inteira a partir de um motivo curto (uma ideia de poucas notas),
desenvolvido através de transformações: transposição (a mesma forma em
outra altura), inversão (a mesma forma de cabeça para baixo) e
retrógrado (a mesma forma de trás para frente). Este módulo usa essas
três transformações sobre a progressão I-IV-V-I (dos módulos 06 e 12)
para compor uma peça curta, e a arranja para 6 instrumentos.

## O que o script faz

`build_events_voz()` gera a melodia: o motivo original sobre o I,
transposto sobre o IV, invertido sobre o V, e em retrógrado sobre o I
final -- as transformações são calculadas em graus de escala (não
semitons), o que garante que tudo continue dentro do tom automaticamente.
As outras cinco funções (`build_events_piano`, `build_events_baixo`,
`build_events_bateria`, `build_events_guitarra`, `build_events_cordas`)
constroem os outros instrumentos sobre a mesma harmonia. `main()` escreve
as 6 faixas no REAPER.

## Como as partes conversam

Cada instrumento tem um papel diferente, deliberadamente, para que eles
não dupliquem a mesma função:

- **Baixo** sustenta a fundamental; **Bateria** trava o groove com ele --
  o bumbo cai exatamente quando o baixo muda de nota.
- **Piano** toca a harmonia em blocos; **Guitarra** toca a mesma harmonia
  em arpejo rápido -- mesma informação harmônica, textura diferente, para
  não soarem redundantes.
- **Cordas** sustentam só a 3ª e a 5ª de cada acorde (não a fundamental,
  que já está no baixo e no piano) -- um pad que preenche sem duplicar.
- **Voz** carrega a melodia principal (o motivo e suas transformações)
  por cima de tudo isso.

## Prática com voz e teclado MIDI (opcional)

Depois de rodar o script, experimente: arme uma faixa nova no REAPER,
conecte um teclado MIDI (ou um microfone, pra cantar), aperte gravar
(usando a interface normal do REAPER -- nenhuma automação nova é
necessária aqui) e toque ou cante uma das partes que você acabou de
aprender -- por exemplo, a linha de baixo, ou a melodia da voz. Compare
o que você tocou com a versão gerada por código.

## O que esperar no piano roll

Seis faixas, todas com 8 segundos de duração, tocando juntas: uma
melodia com 4 frases de 4 notas cada (voz), acordes em bloco (piano),
notas longas graves (baixo), um padrão de bateria repetido 4 vezes,
um arpejo rápido (guitarra) e um pad de duas notas sustentadas (cordas).
Adicione um instrumento (VST) em cada faixa -- o nome do plugin depende
do que está instalado na sua máquina.
