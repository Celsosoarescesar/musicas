# Caelum -- album baseado na vida real do autor (2026-10-04)

**Substitui** o conceito "pastor/politico/amor que engana" (spec `2026-10-03-caelum-album-realismo-design.md`)
e o arco de sentimentos genericos proposto em 2026-10-04. Esta e a fonte da verdade
do album: **cada faixa guarda um sentimento ligado a uma parte real da historia do autor.**

## Nome e ideia

**Caelum** ("ceu" em latim). O ceu da ideia de esperanca: apesar de tudo, ainda ha
esperanca de encontrar um lugar melhor. Album 1 = a historia real ate aqui;
o final nao fecha tudo, aponta para o ceu. O proprio ato de criar este album e a
alegria atual do autor.

## Fatos da vida (dados pelo autor; nao inventar alem disso)

- 45 anos. Vai de **moto** para o trabalho todos os dias; o trabalho e **chato e repetitivo**, nao gosta de ir.
- **Divorciado**: ficou casado mais de 10 anos; o casamento nao deu certo porque e **estéril e nao pode ter filhos**.
- Comecou a **faculdade e parou**; ficou **mais de 8 anos sem estudar**; se sentia **incapaz** porque nao conseguiu acompanhar as aulas.
- Muitos anos **sem um amor**; procura uma pessoa que o **compreenda**.
- Passou pela **pandemia**: ficou muito tempo em casa, sem vontade de sair, com **depressao**.
- **Nao tem amigos**; vive na **solidao**.
- Teve uma **banda de rock** quando jovem, que nao deu certo. O **sonho** e ser **cantor profissional** e viver da propria arte.
- Hoje a **alegria** e fazer o que esta fazendo: **criar musica**.

## Arco: um sentimento por parte da vida

O tom, o bpm e o peso sonoro de cada faixa seguem o plano da `BIBLIA.md` (sobe por quintas,
volta ao D menor na 10). O arco vai do isolamento ate a esperanca.

| # | Tom / bpm | Pasta | Titulo | Parte da vida | Sentimento | Imagem unica |
|---|---|---|---|---|---|---|
| 01 | D / 100 | `01_sozinho` | Sozinho | Sem amigos, vida na solidao | Solidao | Highway a noite, banco vazio (letra ja feita) |
| 02 | A / 96 | `02_rotina` | Rotina | Moto para o trabalho chato, todo dia | Piloto automatico, tedio | Programa que roda o mesmo dia (ja feita; ajustar cena para a moto se o autor quiser) |
| 03 | E / 88 | `03_o_que_nao_veio` | (titulo de trabalho) | Fim do casamento de 10+ anos; esterilidade | Luto pelo que nao veio; culpa que nao e culpa | Quarto vazio / a casa depois (faixa mais leve, sussurrada) |
| 04 | B / 108 | `04_barulho` | Barulho | Faculdade abandonada, 8 anos sem estudar | Sentir-se incapaz | A voz de dentro que diz "voce nao consegue" (letra a ajustar para este fato) |
| 05 | F# / 92 | `05_vazio` | (titulo de trabalho) | Pandemia em casa, depressao | Vazio, peso, sem vontade | Janela fechada, dia que nao passa (a faixa mais pesada e arrastada) |
| 06 | C# / 120 | `06_tempo_perdido` | (titulo de trabalho) | Anos perdidos, 45 anos | Raiva do tempo perdido | Relogio, pressa (a mais rapida; gang vocals) |
| 07 | F# / 112 | `07_alguem_ai` | (titulo de trabalho) | Anos sem amor; procura quem o compreenda | Desejo de ser entendido por alguem | "Alguem ai?" (hino, refrao grande) |
| 08 | B / 98 | `08_recomeco` | (titulo de trabalho) | Criar musica hoje | Alegria, recomeco (centro do album) | Primeira nota, o dedo na tecla (refrao limpo mais importante) |
| 09 | E / 104 | `09_tarde_demais` | (titulo de trabalho) | Banda que nao deu certo; sonho de ser cantor aos 45 | Medo de ser tarde demais | O palco que ficou no passado |
| 10 | D / 100 | `10_caelum` | Caelum | Esperanca | Esperanca / ceu | Volta a highway da 01, agora olhando para cima |

Os titulos de trabalho sao confirmados com o autor, uma faixa por vez.
Pastas renomeadas em 2026-10-04 (01-03 com o REAPER fechado; caminhos em `songs.db` e nos .RPP corrigidos). A pasta 03 usa titulo provisorio.

## Regras de escrita (valem para todas as faixas)

- Primeira pessoa, uma imagem unica por faixa, sem vilao e sem narrador.
- Linhas curtas (ate 10 silabas), estrutura que varia entre as faixas (como 01, 02 e 03).
- Nu metal: verso baixo, refrao limpo e melodico, grito em ponte ou refrao quando o sentimento pede (nenhum na 03).
- **Guarda de abordagem:** a historia e do proprio autor, mas **sem nomes** e sem detalhes que identifiquem
  pessoas reais (ex-esposa, familia, colegas, empresa). O "voce" das letras e figurado.
- **Cuidado com depressao (05):** a letra nomeia o vazio e o peso, sem romantizar e sem sugerir autolesao.
- **Esterilidade (03):** tratar com respeito, sem culpar ninguem e sem humor.
- Letra PT e a fonte da verdade; EN e adaptacao natural (o autor nao domina ingles; Claude faz a folha de pronuncia).

## Fluxo por faixa

1. Titulo e cena combinados com o autor. 2. Letra PT. 3. Aprovacao. 4. EN + pronuncia + `faixa.toml`.
5. Testes. 6. Geracao no ACE-Step (`caelum_gerar`). 7. Stems depois, so se gostar (`scripts/caelum_stems.py`).

Merge unico na `main` depois da gravacao (decisao do autor), nao antes.
