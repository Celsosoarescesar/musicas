# Caelum -- Revisao de conceito (do alegorico para o real) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a alegoria medieval (Ordem Grave, executor, alquimia) por cenas reais nos arquivos do album: renomear 4 pastas, reescrever o contexto das cenas e a biblia, e travar com testes (slugs + varredura de termos antigos).

**Architecture:** So dados e testes (nenhum codigo de producao muda). Task 1 renomeia pastas, atualiza o contexto da cena de 02-10 e a tabela do arco da biblia, com os testes de slug. Task 2 reescreve o resto de `caelum/BIBLIA.md` e o README e adiciona um teste de varredura que impede a volta do vocabulario alegorico (isentando as faixas 01 e 02, cujas letras serao refeitas com o usuario em sessoes interativas, fora deste plano).

**Tech Stack:** Python 3.11+, pytest, `uv`, git.

**Spec:** `docs/superpowers/specs/2026-10-03-caelum-album-realismo-design.md` (revisa `2026-10-03-caelum-album-biblia-design.md`).

## Global Constraints

- Tons, BPM, peso, escalas, mantra e producao hibrida NAO mudam (mesma tabela por posicao). Nenhum `faixa.toml` muda de conteudo (so a pasta pode mudar de nome).
- Slugs novos (fonte da verdade): `01_quebra_de_fe`, `02_obedecer`, `03_silencio`, `04_pastor`, `05_veneno`, `06_promessas`, `07_do_outro_lado`, `08_monstros`, `09_fora_do_sistema`, `10_caelum`. Renomear com `git mv`: `02_executor`->`02_obedecer`, `04_a_mao_que_me_fez`->`04_pastor`, `05_culpa`->`05_veneno`, `06_revolta`->`06_promessas`.
- Vocabulario novo: sistema de fe e poder (pastor, politico, relacao), "o sistema"; criticar o **mecanismo de controle**, sem nomear pessoas, igrejas ou partidos reais. Termos alegoricos proibidos fora das pastas isentas: `ordem grave`, `executor`, `alquimia`, `lamina`, `lâmina`, `cacador`.
- Texto de arquivos de `caelum/` e dos testes em portugues **sem acentos** (estilo do repo), exceto onde um arquivo ja tem acentos (nao introduzir acentos novos em arquivos que nao os tem).
- Nao tocar: `caelum/faixa.py`, `caelum/gerar.py`, `scripts/`, `reaper_bridge/`, `caelum/01_quebra_de_fe/` (letras e pronuncia da 01 e da 02 sao refeitas depois, com o usuario), arquivos de `saida/` (gitignored; `git mv` leva a pasta inteira, saida inclusive).
- Comandos Python com `uv run` a partir da raiz `C:\estudos\daw_music_studio`; no Windows scripts soltos precisam de `PYTHONPATH=. PYTHONUTF8=1`.
- Commits terminam com a linha: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Fora do escopo: reescrever letras (01 e 02 sao sessoes interativas), regerar audio, gravar, mix/master, album 2, qualquer codigo novo.

## Review Focus

1. Referencia velha a um slug renomeado (`02_executor`, `04_a_mao_que_me_fez`, `05_culpa`, `06_revolta`) em arquivo de `caelum/` ou nos testes: os testes de slug e a varredura devem falhar apontando o arquivo.
2. `git mv` de pasta com `saida/` gitignored: a pasta `caelum/02_obedecer/saida/` deve existir depois (audio da Musica #1 da faixa 02) e a antiga `caelum/02_executor/` nao pode sobrar vazia.
3. Termo alegorico esquecido em `caelum/BIBLIA.md`, no README ou em `faixa.toml`/`letra_pt.md` de 03-10: a varredura deve pegar (e a isencao de 01 e 02 deve ser explicita, por nome de pasta, com comentario dizendo quando sai).
4. Varredura que passa por engano: ela precisa varrer arquivos `.md` e `.toml` de `caelum/` recursivamente, sem entrar em `saida/` nem `__pycache__`, e falhar de verdade se um termo proibido for injetado (mutacao documentada no relatorio).
5. `BIBLIA.md` com BPM/tom diferente da tabela por posicao: o teste por linha ja existente deve continuar pegando.

---

## Mapa de arquivos

| Arquivo | Acao | Responsabilidade |
|---|---|---|
| `caelum/02_executor` -> `caelum/02_obedecer` (+ 04, 05, 06) | Rename (Task 1) | slugs novos |
| `caelum/{02..10}_*/letra_pt.md` | Modify (Task 1) | contexto da cena em vocabulario real (corpo da letra intacto) |
| `caelum/BIBLIA.md` | Modify (Task 1: tabela do arco; Task 2: restante) | biblia revisada |
| `tests/test_caelum_biblia.py` | Modify (Tasks 1 e 2) | slugs novos, `UNWRITTEN`, testes da biblia, varredura |
| `caelum/README.md` | Modify (Task 2) | exemplo de slug e referencia a spec nova |

---

### Task 1: Renomear pastas, contexto das cenas e tabela do arco

**Files:**
- Rename (git mv): `caelum/02_executor`, `caelum/04_a_mao_que_me_fez`, `caelum/05_culpa`, `caelum/06_revolta`
- Modify: `caelum/{02_obedecer,03_silencio,04_pastor,05_veneno,06_promessas,07_do_outro_lado,08_monstros,09_fora_do_sistema,10_caelum}/letra_pt.md` (so o trecho antes de `## Letra`)
- Modify: `caelum/BIBLIA.md` (so a tabela do arco: o bloco entre a linha `| Ato | # | Pasta | Cena | "Monstro" quer dizer |` e a linha em branco seguinte)
- Modify: `tests/test_caelum_biblia.py` (lista `BIBLIA`, lista `UNWRITTEN`)

**Interfaces:**
- Consumes: `CAELUM_ROOT`, `load_faixa`, `FaixaError` (ja existem); os testes `test_album_has_exactly_the_ten_track_folders`, `test_faixa_toml_matches_biblia`, `test_written_tracks_load_completely`, `test_unwritten_tracks_*` e `test_biblia_document_covers_every_track_and_the_two_axes` de `tests/test_caelum_biblia.py`.
- Produces: pastas com os slugs novos; `BIBLIA` (lista `(slug, bpm, keyscale)`) e `UNWRITTEN` com os slugs novos, que a Task 2 reutiliza.

- [ ] **Step 1: Atualizar os slugs nos testes (RED)**

Em `tests/test_caelum_biblia.py`, na lista `BIBLIA`, troque os quatro slugs (BPM e tom iguais):

```python
    ("02_obedecer", 96, "A minor"),
    ("03_silencio", 88, "E minor"),
    ("04_pastor", 108, "B minor"),
    ("05_veneno", 92, "F# minor"),
    ("06_promessas", 120, "C# minor"),
```

e na lista literal `UNWRITTEN` troque `"04_a_mao_que_me_fez"` por `"04_pastor"`, `"05_culpa"` por `"05_veneno"` e `"06_revolta"` por `"06_promessas"` (a `02` NAO esta em `UNWRITTEN`: ja tem `letra_en.md` real).

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: FAIL -- `test_album_has_exactly_the_ten_track_folders` e varios parametrizados com `FileNotFoundError` (pastas novas ainda nao existem).

- [ ] **Step 3: Renomear as pastas**

```bash
git mv caelum/02_executor caelum/02_obedecer
git mv caelum/04_a_mao_que_me_fez caelum/04_pastor
git mv caelum/05_culpa caelum/05_veneno
git mv caelum/06_revolta caelum/06_promessas
```

Expected: nenhuma pasta antiga sobra (`ls caelum` mostra so os slugs novos, `_modelo`, `01_quebra_de_fe`, 03, 07-10); `caelum/02_obedecer/saida/` continua existindo com os arquivos da Musica #1 da faixa 02 (conferir com `ls caelum/02_obedecer/saida`). Se uma pasta antiga ainda existir (so `saida/` ignorada), apague apenas essa sobra vazia depois de conferir que o conteudo ja esta na pasta nova.

- [ ] **Step 4: Reescrever o contexto da cena de 02-10 (script temporario)**

Crie `make_contextos.py` no scratchpad da sessao (nao no repo) e rode da raiz com `PYTHONPATH=. PYTHONUTF8=1 uv run python <scratchpad>/make_contextos.py`:

```python
from pathlib import Path

ROOT = Path("caelum")

# slug, titulo, cena, monstro, voz, escala
FAIXAS = [
    ("02_obedecer", "Obedecer",
     "Caelum cresce obedecendo o que mandam, no pulpito e em casa, com orgulho de ser um bom membro; a primeira duvida aparece (flashback, antes da quebra de fe).",
     "monstro e quem manda sem dar razao e chama de rebelde quem pergunta.",
     "verso falado, refrao limpo, grito curto; o mantra 'Obey. Don't ask.' sussurrado.",
     "A minor -- A menor; menor harmonica na voz do sistema (mantra, pre-refrao), natural nos riffs."),
    ("03_silencio", "Silencio",
     "Caelum nota os sinais de que algo esta errado (dinheiro, favores, castigos) e cala para nao perder o lugar e a comunidade (flashback).",
     "o silencio de quem ve alimenta quem manipula.",
     "sussurro e voz limpa, SEM grito; a faixa mais contida do album.",
     "E minor -- E menor; menor harmonica nos trechos do sistema, natural no resto."),
    ("04_pastor", "Pastor",
     "Caelum sente raiva do falso pastor que vive do sofrimento e do dinheiro de quem acredita nele.",
     "monstro e quem lucra com a dor alheia em nome da fe.",
     "refrao alterna voz limpa e grito; breakdown antes do refrao final.",
     "B minor -- B menor natural (raiva); sem harmonica."),
    ("05_veneno", "Veneno",
     "Caelum foi enganado por quem dizia amar: o relacionamento que nao deu certo e a mesma mentira em escala pequena.",
     "monstro e quem usa o amor como arma.",
     "voz limpa e grito alternados ja nos versos; a faixa mais suja e arrastada, a dor do amor.",
     "F# minor -- F# menor natural; sem harmonica."),
    ("06_promessas", "Promessas",
     "Caelum olha para os politicos que roubam a nacao e vendem promessas ao povo; a raiva publica. Ponto mais distante de casa no plano de tons.",
     "monstro e quem rouba e promete.",
     "gang vocals e grito forte; breakdown seco antes do refrao final.",
     "C# minor -- C# menor natural; a faixa mais rapida (120 bpm)."),
    ("07_do_outro_lado", "Do outro lado",
     "Caelum percebe que nao esta sozinho: ha muita gente enganada e julgada pelo mesmo sistema, e se une a ela.",
     "os rotulados sao os enganados, nao os culpados.",
     "coro (os enganados) no refrao grande e cantavel; lider limpo.",
     "F# minor -- F# menor natural nos riffs; menor melodica no refrao (6a e 7a elevadas subindo, decisao do usuario); comeca a volta por quartas."),
    ("08_monstros", "Monstros",
     "Caelum entende quem e quem: o monstro nao e quem acorda, e quem manipula (o pastor que lucra, o politico que rouba, quem mente no amor). Centro do album.",
     "VIRADA: o rotulo se inverte; o verdadeiro monstro e quem controla o sistema.",
     "refrao limpo, o mais importante do album; mantra invertido 'Ask. Don't obey.'.",
     "B minor -- B menor; menor melodica no refrao (6a e 7a elevadas subindo) e no mantra invertido."),
    ("09_fora_do_sistema", "Fora do sistema",
     "Caelum e julgado por quem ainda vive dentro do sistema (igreja, familia, conhecidos); quem julga tambem foi enganado.",
     "quem esta dentro o chama de monstro; ele sabe quem e o monstro de verdade.",
     "verso falado, refrao limpo, grito curto; o sistema como textura eletronica fria.",
     "E minor -- E menor natural nos riffs; melodica nas melodias de refrao."),
    ("10_caelum", "Caelum",
     "Faixa-titulo: quem Caelum se tornou, vivendo do seu jeito, julgado e assumido. Fecha o circulo: volta ao tom e BPM da faixa 01.",
     "assume o rotulo sem aceitar o significado.",
     "refrao limpo gigante, grito final; mantra invertido.",
     "D minor -- D menor, mesmo tom da 01 (la, o sistema; aqui, o proprio Caelum); melodica no refrao."),
]

for slug, titulo, cena, monstro, voz, escala in FAIXAS:
    path = ROOT / slug / "letra_pt.md"
    text = path.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    body = text[text.index("## Letra"):]
    head = (
        f"# {titulo} -- letra em portugues (fonte da verdade){nl}{nl}"
        f"Contexto da cena (o que acontece, o que Caelum sente):{nl}{nl}"
        f"- {cena}{nl}"
        f"- 'Monstro' aqui quer dizer: {monstro}{nl}"
        f"- Voz: {voz}{nl}"
        f"- Tom e escala: {escala}{nl}{nl}"
    )
    path.write_text(head + body, encoding="utf-8")
print("ok:", [f[0] for f in FAIXAS])
```

Expected: imprime `ok: [...]` com 9 slugs; `git diff --stat` mostra 9 arquivos `letra_pt.md` alterados so no cabecalho (a letra da 02 continua no corpo, ainda do conceito antigo, e sera refeita com o usuario). Nada em `caelum/01_quebra_de_fe/` mudou.

- [ ] **Step 5: Atualizar a tabela do arco em `caelum/BIBLIA.md`**

Substitua as linhas da tabela do arco (da linha `| Ato | # | Pasta | Cena | "Monstro" quer dizer |` ate a ultima linha da tabela, `| | 10 | ... |`) por exatamente:

```markdown
| Ato | # | Pasta | Cena | "Monstro" quer dizer |
|---|---|---|---|---|
| Fe | 01 | `01_quebra_de_fe` (pronta) | Descobre que o pastor em quem confiava vive do sofrimento dos outros | O pastor que lucra com a fe |
| | 02 | `02_obedecer` | Crescer fazendo o que mandam, sem perguntar | Quem manda sem dar razao |
| | 03 | `03_silencio` | Ve os sinais e cala para nao perder o lugar | O silencio alimenta o sistema |
| Ruptura | 04 | `04_pastor` | Raiva do falso pastor que lucra com a dor | Quem vive do sofrimento alheio |
| | 05 | `05_veneno` | O amor que nao deu certo: enganado por quem dizia amar | Quem usa o amor como arma |
| | 06 | `06_promessas` | Politicos que roubam a nacao; a promessa vendida ao povo | Quem rouba e promete |
| | 07 | `07_do_outro_lado` | Percebe que nao esta sozinho: muita gente enganada e julgada | Os rotulados sao os enganados |
| Nova realidade | 08 | `08_monstros` | O monstro nao e quem acorda, e quem manipula | **Virada:** quem controla o sistema |
| | 09 | `09_fora_do_sistema` | E julgado por quem ainda vive dentro dele | Quem esta dentro o chama de monstro |
| | 10 | `10_caelum` | Faixa-titulo: quem se tornou, julgado e assumido | Assume o rotulo sem aceitar o significado |
```

- [ ] **Step 6: Rodar e ver passar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: todos passam (a tabela do plano sonoro da biblia ainda usa numero de posicao, sem slug, entao nao muda).

- [ ] **Step 7: Suite completa**

Run: `uv run pytest -q`
Expected: so as 8 falhas ambientais conhecidas (REAPER fechado) ou nenhuma; nenhuma falha nova.

- [ ] **Step 8: Commit**

```bash
git add -A caelum tests/test_caelum_biblia.py
git commit -m "$(cat <<'EOF'
refactor: slugs e cenas reais das faixas 02-10 (revisao de conceito)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

Antes do commit, rode `git status --short`: so devem aparecer renomeacoes (`R`), os `letra_pt.md` e a biblia/testes; nada de `saida/` (ignorado) e nada em `caelum/01_quebra_de_fe/`.

---

### Task 2: Biblia reescrita, README e varredura de vocabulario

**Files:**
- Modify: `caelum/BIBLIA.md` (substituir o arquivo inteiro)
- Modify: `caelum/README.md` (exemplos de slug e a spec nova)
- Modify: `tests/test_caelum_biblia.py` (ajustar `test_biblia_document_covers_every_track_and_the_two_axes`; acrescentar a varredura)

**Interfaces:**
- Consumes: `BIBLIA`, `UNWRITTEN`, `CAELUM_ROOT` de `tests/test_caelum_biblia.py` (Task 1) e as pastas renomeadas.
- Produces: `PENDING_REWRITE` (tupla de pastas isentas da varredura) e `FORBIDDEN_TERMS` em `tests/test_caelum_biblia.py`.

- [ ] **Step 1: Escrever os testes (RED)**

Em `tests/test_caelum_biblia.py`, no teste `test_biblia_document_covers_every_track_and_the_two_axes`, troque as quatro ultimas assercoes (as que olham `"executor"`, `"quem e o monstro"`, os dois mantras e `"ReaAssist"`) por:

```python
    lowered = text.lower()
    assert "obediencia sem questionar" in lowered
    assert "quem e o monstro" in lowered
    assert "mecanismo de controle" in lowered
    assert "Obey. Don't ask." in text and "Ask. Don't obey." in text
    assert "ReaAssist" in text
```

e acrescente no fim do arquivo:

```python
# Vocabulario da alegoria medieval, trocado por cenas reais na revisao de
# conceito (docs/superpowers/specs/2026-10-03-caelum-album-realismo-design.md).
FORBIDDEN_TERMS = ("ordem grave", "executor", "alquimia", "lamina", "lâmina", "cacador")

# Pastas cujas letras ainda sao do conceito antigo e serao refeitas com o
# usuario (uma sessao por faixa). Tire a pasta daqui quando a letra nova for
# aprovada e commitada.
PENDING_REWRITE = ("01_quebra_de_fe", "02_obedecer")


def _album_text_files():
    for path in sorted(CAELUM_ROOT.rglob("*")):
        if path.suffix not in (".md", ".toml") or not path.is_file():
            continue
        rel = path.relative_to(CAELUM_ROOT)
        if "saida" in rel.parts or "__pycache__" in rel.parts:
            continue
        if rel.parts[0] in PENDING_REWRITE:
            continue
        yield rel, path.read_text(encoding="utf-8-sig").lower()


def test_no_allegorical_vocabulary_outside_pending_rewrites():
    offenders = [
        f"{rel}: '{term}'"
        for rel, text in _album_text_files()
        for term in FORBIDDEN_TERMS
        if term in text
    ]
    assert not offenders, "vocabulario alegorico encontrado: " + "; ".join(offenders)


def test_scan_actually_covers_biblia_readme_and_tracks():
    scanned = {str(rel).replace("\\", "/") for rel, _ in _album_text_files()}
    assert "BIBLIA.md" in scanned and "README.md" in scanned
    assert "03_silencio/letra_pt.md" in scanned and "10_caelum/faixa.toml" in scanned
    assert not any(p.startswith(("01_quebra_de_fe/", "02_obedecer/")) for p in scanned)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: FAIL -- `test_biblia_document_covers_every_track_and_the_two_axes` (faltam `obediencia sem questionar`/`mecanismo de controle` na biblia atual) e `test_no_allegorical_vocabulary_outside_pending_rewrites` (BIBLIA.md e README ainda citam `executor`/`Ordem Grave`).

- [ ] **Step 3: Reescrever `caelum/BIBLIA.md`**

Substitua o conteudo inteiro do arquivo por exatamente:

````markdown
# Caelum -- biblia do album 1

Specs: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md` (estrutura, plano sonoro)
e `docs/superpowers/specs/2026-10-03-caelum-album-realismo-design.md` (conceito real, que
substitui as cenas da spec anterior). Como usar as pastas: `caelum/README.md`.

## Conceito

**Caelum** (latim: "ceu") e o autor em primeira pessoa: cresceu olhando para
cima, dentro de um sistema de fe e poder, obedeceu sem perguntar, descobriu
como esse sistema usa as pessoas, saiu e vive do seu jeito, julgado por quem
ainda esta dentro. A historia parte da vivencia do usuario (falsos pastores,
politicos, relacionamentos); as faixas misturam confissao direta e
personagem, sem nomear pessoas, igrejas ou partidos reais.

Eixos em todas as faixas:

1. **Obediencia sem questionar:** o membro que faz o que mandam.
2. **Quem e o monstro.** O sistema chama de "perdido", "rebelde" ou "inimigo"
   quem acorda. A virada: os verdadeiros monstros sao quem manipula (o pastor
   que vive do sofrimento dos outros, o politico que rouba a nacao, quem
   mente no amor), nao quem acorda. Quem julga Caelum tambem e vitima do
   mesmo controle. Aparecem nas letras como "voces"/"eles", sem rosto fixo.
3. **Varias formas de ser enganado:** por lideres de fe, por politicos, por
   quem se ama.

**Guarda de abordagem:** a critica e ao **mecanismo de controle** (quem
manipula e lucra com fe, medo, culpa e esperanca), nao as pessoas que
acreditam. Figuras genericas, sem nomes reais.

**Final (album 1): caminho do meio.** O sistema continua; Caelum vive livre
fora dele e aceita ser julgado. A historia segue num album 2.

Genero: nu metal melodico, vocal limpo + grito, sem rap, uma voz so (Caelum,
primeira pessoa), sem narrador.

## Arco e faixas

As faixas 02-03 sao flashback (a 01 abre pelo ponto de virada). As letras
das faixas 01 e 02 foram escritas no conceito antigo (alegorico) e sao
refeitas com o usuario no conceito real.

| Ato | # | Pasta | Cena | "Monstro" quer dizer |
|---|---|---|---|---|
| Fe | 01 | `01_quebra_de_fe` (pronta) | Descobre que o pastor em quem confiava vive do sofrimento dos outros | O pastor que lucra com a fe |
| | 02 | `02_obedecer` | Crescer fazendo o que mandam, sem perguntar | Quem manda sem dar razao |
| | 03 | `03_silencio` | Ve os sinais e cala para nao perder o lugar | O silencio alimenta o sistema |
| Ruptura | 04 | `04_pastor` | Raiva do falso pastor que lucra com a dor | Quem vive do sofrimento alheio |
| | 05 | `05_veneno` | O amor que nao deu certo: enganado por quem dizia amar | Quem usa o amor como arma |
| | 06 | `06_promessas` | Politicos que roubam a nacao; a promessa vendida ao povo | Quem rouba e promete |
| | 07 | `07_do_outro_lado` | Percebe que nao esta sozinho: muita gente enganada e julgada | Os rotulados sao os enganados |
| Nova realidade | 08 | `08_monstros` | O monstro nao e quem acorda, e quem manipula | **Virada:** quem controla o sistema |
| | 09 | `09_fora_do_sistema` | E julgado por quem ainda vive dentro dele | Quem esta dentro o chama de monstro |
| | 10 | `10_caelum` | Faixa-titulo: quem se tornou, julgado e assumido | Assume o rotulo sem aceitar o significado |

A 08 e o centro do album: o refrao dela e o mais importante para a inversao
do "monstro".

## Plano sonoro

Subir por quintas (mais sustenidos) soa como tensao e afastamento de casa;
descer por quartas, como assentar e voltar. O album se afasta ao maximo do
D menor da 01 (na 06, C# menor) e volta a ele na 10.

| # | Tom | BPM | Peso | Voz |
|---|---|---|---|---|
| 01 | D menor | 100 | Medio | Verso contido, refrao limpo, ponte gritada |
| 02 | A menor | 96 | Medio | Verso falado, refrao limpo, grito curto; groove "marcha" |
| 03 | E menor | 88 | Leve | Sussurro e limpo, sem grito |
| 04 | B menor | 108 | Pesado | Refrao alterna limpo e grito; riff sincopado |
| 05 | F# menor | 92 | Muito pesado | Limpo e grito alternados; a mais suja (a dor do amor) |
| 06 | C# menor | 120 | O mais rapido | Gang vocals, grito forte; breakdown (raiva publica) |
| 07 | F# menor | 112 | Pesado, anthem | Coro (os enganados), refrao grande |
| 08 | B menor | 98 | Medio | Refrao limpo, o mais importante; mantra invertido |
| 09 | E menor | 104 | Medio | Verso falado, refrao limpo, grito curto |
| 10 | D menor | 100 | Medio a pesado | Refrao gigante, grito final; volta ao tom/BPM da 01 |

Valores sao pontos de partida; ajuste de ouvido na geracao.

### Escalas

- **Menor natural:** base dos riffs de todas as faixas.
- **Menor harmonica (7a elevada):** a voz do sistema (mantra, pre-refrao e ponte nas faixas 01-03).
- **Menor melodica (6a e 7a elevadas, subindo):** melodias de refrao do ato 3 e o refrao da 07 (a uniao dos enganados, decisao do usuario); esperanca; mantra invertido.

O ACE-Step so recebe o tom (`keyscale`) e nao distingue harmonica de
melodica; isso fica na melodia que voce grava e na camada REAPER.

### Motivos

- **Mantra da obediencia:** "Obey. Don't ask." sussurrado/monotono nas
  faixas 01-03; invertido, "Ask. Don't obey.", nas 08-10. E a voz de qualquer
  sistema que pede obediencia (pulpito, palanque, relacao abusiva). Gravado
  com a sua voz no REAPER.
- **Curva do grito:** nenhum na 03, maximo nas 05 e 06, contido nas 08-10.
- **Breakdown** nas faixas 04, 06 e 07.
- **Prompt-base comum:** os dez prompts compartilham a base "melodic nu
  metal, downtuned 7-string guitars, ..., no rap"; cada faixa varia so BPM,
  tom, peso e textura.
- **Linguagem do genero:** frases curtas e diretas, confessionais; ganchos
  repetidos; contraste verso falado, refrao aberto, grito na ponte.

## Producao hibrida

**Camada 1 -- ACE-Step (Kaggle):** banda (bateria, baixo, guitarras de 7
cordas), estrutura, groove, peso do refrao e vocal guia; Demucs separa os
stems.

**Camada 2 -- REAPER:** mantra da obediencia, texturas e transicoes
(glitches, risers, pads frios, impactos), scratches/samples (se voce tiver ou
gravar), tratamento da voz (grito, dobros, efeitos por ato) e edicoes
(breakdown, ganchos repetidos).

Capacidades do `reaper_bridge`:

- **Ja existem (verificadas):** volume, pan, FX, importar audio, aplicar
  master, renderizar, montar a sessao vocal.
- **Nao verificadas ao vivo (so entram quando uma faixa precisar, sempre
  confirmadas em faixas temporarias novas):** posicionar itens na linha do
  tempo, envelopes, recortar/dividir itens, criar samples. Ate la, sao
  trabalho manual no REAPER.

O ReaAssist (assistente em Lua para o REAPER) nao e recriado aqui: a
licenca e "all rights reserved" (sem redistribuicao nem obra derivada), ele
so funciona como janela de chat dentro do REAPER e exige chave de API paga.
Voce pode instalar e usar por conta propria, sem ligacao com o repositorio.

## Fichas das faixas

Cada pasta `caelum/NN_slug/` tem `faixa.toml` (prompt, BPM, tom) e
`letra_pt.md` com o contexto da cena. `letra_en.md` e `pronuncia.md` das
faixas ainda nao escritas sao feitos na producao de cada uma (o
`caelum_gerar` recusa gerar enquanto a `letra_en.md` for o modelo).

Camada REAPER por faixa ([MCP] = ja da para fazer com as ferramentas
atuais; [manual] = no REAPER, por enquanto):

| # | Camada REAPER |
|---|---|
| 01 | Mantra sussurrado ao fundo do verso [MCP: faixa + FX; posicionar: manual] |
| 02 | Mantra falado, voz de pulpito; textura seca e ritmada [manual] |
| 03 | Texturas frias e silencios [manual]; reverb/delay na voz [MCP] |
| 04 | Breakdown: corte/repeticao de trecho [manual] |
| 05 | Saturacao extra no baixo e na voz [MCP: FX] |
| 06 | Breakdown seco antes do refrao final [manual]; gang vocals dobrados [MCP; alinhar/posicionar: manual] |
| 07 | Coro de vozes empilhadas no refrao [MCP: faixas + pan] |
| 08 | Mantra invertido "Ask. Don't obey." (sua voz, melodica) [MCP + manual] |
| 09 | Texturas eletronicas frias / glitches [manual] |
| 10 | Mantra invertido + camada final de coro; master [MCP: apply_master_chain; alinhar/posicionar: manual] |
````

- [ ] **Step 4: Atualizar `caelum/README.md`**

Troque no arquivo, preservando o resto:

- a linha `` `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md`) `` do paragrafo da biblia por `` `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md` e `2026-10-03-caelum-album-realismo-design.md`). ``
- todas as ocorrencias de `02_executor` por `02_obedecer`.

Conferir com `grep -n "executor\|02_obedecer" caelum/README.md` (zero `executor`).

- [ ] **Step 5: Rodar e ver passar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: todos passam.

- [ ] **Step 6: Mutacao da varredura (nao commitar)**

Acrescente temporariamente a palavra `alquimia` em `caelum/03_silencio/letra_pt.md`, rode `uv run pytest tests/test_caelum_biblia.py -q` e confirme que `test_no_allegorical_vocabulary_outside_pending_rewrites` FALHA citando `03_silencio\letra_pt.md` (ou barra normal). Reverta com `git checkout -- caelum/03_silencio/letra_pt.md` (a pasta nao tem outras alteracoes nao commitadas nesta altura; confira `git status --short` antes). Cole a saida real no relatorio.

- [ ] **Step 7: Suite completa**

Run: `uv run pytest -q`
Expected: so as 8 falhas ambientais conhecidas (REAPER fechado) ou nenhuma; nenhuma falha nova.

- [ ] **Step 8: Commit**

```bash
git add caelum/BIBLIA.md caelum/README.md tests/test_caelum_biblia.py
git commit -m "$(cat <<'EOF'
docs: biblia e README no conceito real; varredura contra vocabulario alegorico

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```
