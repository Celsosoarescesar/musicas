# Curso de Música com music21 no piano roll do REAPER

Cada lição gera conteúdo musical com [music21](https://music21.org/music21docs/usersGuide/)
e escreve numa faixa dedicada do REAPER, para aprender vendo e ouvindo a
teoria no piano roll em vez de só ler texto.

A teoria de cada módulo combina duas referências:

- **music21 User's Guide** — como programar cada conceito.
- **[Open Music Theory](https://viva.pressbooks.pub/openmusictheory/)**
  (Creative Commons, atribuição obrigatória) — o que o conceito significa
  musicalmente. Os READMEs linkam e resumem os capítulos relevantes com
  as próprias palavras; não copiam o texto do livro.

## Pré-requisitos

1. REAPER aberto.
2. `reapy` configurado (`reapy.configure_reaper()`, rodado a partir do
   ambiente virtual do repo principal — nunca de um worktree).
3. Dependências do projeto instaladas (`uv sync`, na raiz do repositório).

## Como rodar uma lição

```bash
uv run python curso_music21/modulos/01_notas_e_alturas/licao.py
```

Cada lição escreve numa faixa própria (`Curso NN - <nome>`), criando-a se
não existir e limpando notas de uma execução anterior antes de escrever de
novo — pode rodar a mesma lição quantas vezes quiser.

## Módulos (Fase 1)

| # | Módulo |
|---|---|
| 01 | Notas e Alturas |
| 02 | Ritmo: Durações e Compassos |
| 03 | Escalas e Tonalidades |
| 04 | Intervalos |
| 05 | Acordes e Tríades |

O currículo completo (16 módulos, incluindo harmonia funcional, condução
de vozes, contraponto, forma, corpus/análise e o capstone de composição e
arranjo multi-instrumental) está descrito em
`docs/superpowers/specs/2026-09-27-curso-music21-design.md`; os módulos
06-16 chegam em fases de implementação seguintes.
