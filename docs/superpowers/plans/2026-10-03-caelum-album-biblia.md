# Caelum -- Biblia do album (frente 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a biblia do album Caelum: protecao contra letra de modelo, as pastas `caelum/02_*` a `caelum/10_*` prontas (faixa.toml + contexto da cena) e o documento `caelum/BIBLIA.md`.

**Architecture:** Mudanca minima de codigo (um guard em `caelum.faixa.load_faixa`) mais dados versionados (pastas das faixas e a biblia). Um teste de dados (`tests/test_caelum_biblia.py`) trava as pastas contra a tabela da biblia (slug, BPM, tom).

**Tech Stack:** Python 3.11+ (`tomllib`), pytest, `uv`.

**Spec:** `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md` (continua `2026-10-02-caelum-album-design.md`).

## Global Constraints

- Estilo do album: nu metal melodico, vocal limpo + grito, **sem rap** (todo prompt contem `no rap`); uma voz so, Caelum, primeira pessoa, sem narrador.
- Texto de arquivos de `caelum/` e dos testes em portugues **sem acentos** (estilo do repo); a biblia/spec tambem.
- Tabela da biblia (fonte da verdade do plano; BPM e tom exatos):

  | # | slug | BPM | keyscale |
  |---|---|---|---|
  | 01 | `01_quebra_de_fe` (pronta, nao muda) | 100 | `D minor` |
  | 02 | `02_executor` | 96 | `A minor` |
  | 03 | `03_silencio` | 88 | `E minor` |
  | 04 | `04_a_mao_que_me_fez` | 108 | `B minor` |
  | 05 | `05_culpa` | 92 | `F# minor` |
  | 06 | `06_revolta` | 120 | `C# minor` |
  | 07 | `07_do_outro_lado` | 112 | `F# minor` |
  | 08 | `08_monstros` | 98 | `B minor` |
  | 09 | `09_fora_do_sistema` | 104 | `E minor` |
  | 10 | `10_caelum` | 100 | `D minor` |

- Todo `faixa.toml` novo usa so as chaves permitidas (`prompt, duration, seed, bpm, keyscale, vocal_language, lufs_target`), `seed = 42`, `vocal_language = "en"`, `lufs_target = -9.0`, `duration = 180.0` (exceto a 03: `150.0`).
- `letra_en.md` e `pronuncia.md` das faixas 02-10 ficam como o modelo (`caelum/_modelo/`); sao escritas na producao de cada faixa, fora deste plano.
- `ace_step/lyrics.py` nao e usado; a pasta `caelum/01_quebra_de_fe/` nao e alterada.
- Comandos Python com `uv run` a partir da raiz `C:\estudos\daw_music_studio`; no Windows, scripts soltos precisam de `PYTHONPATH=. PYTHONUTF8=1`. Testes mockam REAPER e Kaggle (nenhuma task deste plano os usa).
- Commits terminam com a linha: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Fora do escopo: letras das faixas 02-10, geracao de audio, gravacao, mix/master, album 2, implementar capacidades novas do `reaper_bridge`.

## Review Focus

1. `letra_en.md` com **parte** do texto de modelo (ex.: uma linha `(write the chorus here)` esquecida no meio de uma letra real) ou com caixa diferente (`(Write the ...)`): deve falhar antes de gastar uma geracao do Kaggle, nao so quando a letra inteira e igual ao modelo.
2. `gerar` numa pasta com letra de modelo: nao pode criar `saida/`, `songs.db` nem chamar o pipeline.
3. `faixa.toml` novo cujo `bpm`/`keyscale` diverge da tabela, ou cujo prompt nao contem o mesmo BPM/tom/`no rap`: o teste de dados deve falhar apontando a faixa.
4. Pasta de faixa sem `letra_pt.md` ou com a linha de cena ainda em branco (`- ...`): o teste de dados deve falhar.
5. `letra_en.md` com CRLF ou BOM (Notepad no Windows) e marcador de modelo: a deteccao deve funcionar igual.

---

## Mapa de arquivos

| Arquivo | Acao | Responsabilidade |
|---|---|---|
| `caelum/faixa.py` | Modify (Task 1) | `load_faixa` recusa `letra_en.md` com texto de modelo |
| `tests/test_caelum_faixa.py` | Modify (Task 1) | testes do guard; teste do modelo passa a esperar a recusa |
| `tests/test_caelum_gerar.py` | Modify (Task 1) | `gerar` com letra de modelo falha sem tocar em banco/Kaggle |
| `caelum/02_*` ... `caelum/10_*` | Create (Task 2) | `faixa.toml`, `letra_pt.md`, `letra_en.md`, `pronuncia.md` por faixa |
| `tests/test_caelum_biblia.py` | Create (Task 2) | trava as 10 pastas contra a tabela da biblia |
| `caelum/BIBLIA.md` | Create (Task 3) | biblia: conceito, arco, plano sonoro, fichas |
| `caelum/README.md` | Modify (Task 3) | aponta para a biblia e a spec da frente 2 |
| `tests/test_caelum_biblia.py` | Modify (Task 3) | a biblia cita as 10 faixas |

---

### Task 1: `load_faixa` recusa letra de modelo

**Files:**
- Modify: `caelum/faixa.py` (constante nova + checagem logo depois de ler `lyrics`)
- Modify: `tests/test_caelum_faixa.py` (testes novos; substituir `test_modelo_is_a_loadable_faixa`)
- Modify: `tests/test_caelum_gerar.py` (um teste novo no fim)

**Interfaces:**
- Consumes: `FaixaError`, `load_faixa(faixa_dir) -> Faixa`, `CAELUM_ROOT` (ja existem em `caelum/faixa.py`); `gerar(faixa_dir, ...)` de `caelum/gerar.py`.
- Produces: `load_faixa` levanta `FaixaError` cuja mensagem contem a palavra `modelo` quando `letra_en.md` contem o marcador de modelo `(write ` (sem diferenciar maiusculas). Task 2 usa essa mensagem (`match="modelo"`) para provar que o resto de cada `faixa.toml` novo e valido.

- [ ] **Step 1: Escrever os testes que falham**

Em `tests/test_caelum_faixa.py`, **substitua** o teste `test_modelo_is_a_loadable_faixa` (linhas 70-73) por:

```python
def test_modelo_letra_is_rejected_as_template():
    # O modelo existe para ser copiado; carregar sua letra como se fosse real
    # gastaria uma geracao do Kaggle com "(write the English lyrics here)".
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(CAELUM_ROOT / "_modelo")


@pytest.mark.parametrize(
    "lyrics",
    [
        "[en]\n[Verse]\nreal line\n(write the chorus here)\n[Bridge]\nmore real\n",
        "[en]\n[Verse]\n(Write The English lyrics here)\n",
        "[en]\r\n[Verse]\r\n(write the English lyrics here)\r\n",
    ],
)
def test_load_faixa_rejects_partially_template_lyrics(tmp_path, lyrics):
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(_make_faixa(tmp_path, lyrics=lyrics))


def test_load_faixa_rejects_template_lyrics_with_bom(tmp_path):
    faixa_dir = _make_faixa(tmp_path, lyrics=None)
    (faixa_dir / "letra_en.md").write_bytes(
        b"\xef\xbb\xbf[en]\n[Verse]\n(write the English lyrics here)\n"
    )
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(faixa_dir)


def test_load_faixa_accepts_lyrics_that_merely_mention_writing(tmp_path):
    faixa = load_faixa(_make_faixa(tmp_path, lyrics="[en]\n[Verse]\nI write my name in ash\n"))
    assert "write my name" in faixa.lyrics
```

Em `tests/test_caelum_gerar.py`, acrescente no fim:

```python
def test_gerar_template_lyrics_fail_before_touching_db_or_kaggle(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    (faixa_dir / "letra_en.md").write_text(
        "[en]\n[Verse]\n(write the English lyrics here)\n", encoding="utf-8"
    )
    with patch("caelum.gerar.orchestrator.run_generation") as mock_run:
        with pytest.raises(FaixaError, match="modelo"):
            gerar(faixa_dir)
    mock_run.assert_not_called()
    assert not (faixa_dir / "saida").exists()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/test_caelum_faixa.py tests/test_caelum_gerar.py -q`
Expected: FAIL -- os 6 testes novos de rejeicao (5 em test_caelum_faixa.py, 1 em test_caelum_gerar.py) falham com `DID NOT RAISE` (o teste que aceita "write my name" ja passa).

- [ ] **Step 3: Implementar o guard**

Em `caelum/faixa.py`, depois de `_ALLOWED_KEYS = ...` acrescente:

```python
# Texto dos placeholders de caelum/_modelo/letra_en.md ("(write the ... here)").
_TEMPLATE_LYRICS_MARKER = "(write "
```

E logo depois do bloco `if not lyrics: raise FaixaError(f"{lyrics_path.name} esta vazio")` acrescente:

```python
    if _TEMPLATE_LYRICS_MARKER in lyrics.lower():
        raise FaixaError(
            f"{lyrics_path.name} ainda tem texto de modelo ('{_TEMPLATE_LYRICS_MARKER}...'): "
            "escreva a letra em ingles antes de gerar"
        )
```

- [ ] **Step 4: Rodar e ver passar**

Run: `uv run pytest tests/test_caelum_faixa.py tests/test_caelum_gerar.py -q`
Expected: todos passam, saida sem warnings novos.

- [ ] **Step 5: Suite completa**

Run: `uv run pytest -q`
Expected: so as 8 falhas ja conhecidas (5 em `tests/test_mastering.py` e 3 em `tests/test_project.py`, `AttributeError` do reapy sem REAPER aberto); nenhuma falha nova. Se alguma falha nova aparecer, corrija antes de commitar.

- [ ] **Step 6: Commit**

```bash
git add caelum/faixa.py tests/test_caelum_faixa.py tests/test_caelum_gerar.py
git commit -m "$(cat <<'EOF'
feat: load_faixa recusa letra_en.md com texto de modelo

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Pastas das faixas 02-10 e teste de dados

**Files:**
- Create: `tests/test_caelum_biblia.py`
- Create: `caelum/<slug>/{faixa.toml,letra_pt.md,letra_en.md,pronuncia.md}` para as 9 faixas 02-10 (via script temporario no scratchpad; o script NAO entra no repo)

**Interfaces:**
- Consumes: `load_faixa`, `FaixaError`, `CAELUM_ROOT` (Task 1: a mensagem de erro de letra de modelo contem `modelo`); modelos em `caelum/_modelo/`.
- Produces: 9 pastas validas ate a letra; `BIBLIA` (lista `(slug, bpm, keyscale)` das 10 faixas) e `UNWRITTEN` (slugs 02-10) em `tests/test_caelum_biblia.py`, que Task 3 reutiliza.

- [ ] **Step 1: Escrever o teste de dados (falha porque as pastas nao existem)**

Crie `tests/test_caelum_biblia.py`:

```python
"""Trava as pastas do album contra a tabela da biblia
(docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md)."""

import tomllib

import pytest

from caelum.faixa import CAELUM_ROOT, FaixaError, load_faixa

# (slug, bpm, keyscale) -- fonte da verdade: tabela do plano/biblia.
BIBLIA = [
    ("01_quebra_de_fe", 100, "D minor"),
    ("02_executor", 96, "A minor"),
    ("03_silencio", 88, "E minor"),
    ("04_a_mao_que_me_fez", 108, "B minor"),
    ("05_culpa", 92, "F# minor"),
    ("06_revolta", 120, "C# minor"),
    ("07_do_outro_lado", 112, "F# minor"),
    ("08_monstros", 98, "B minor"),
    ("09_fora_do_sistema", 104, "E minor"),
    ("10_caelum", 100, "D minor"),
]

# Faixas cuja letra_en.md ainda e o modelo. Ao terminar uma faixa, tire o slug
# daqui: ela passa a ser checada por load_faixa completo (ver o teste da 01).
UNWRITTEN = [slug for slug, _, _ in BIBLIA[1:]]


def _toml(slug):
    return tomllib.loads((CAELUM_ROOT / slug / "faixa.toml").read_text(encoding="utf-8-sig"))


def test_album_has_exactly_the_ten_track_folders():
    folders = sorted(p.name for p in CAELUM_ROOT.glob("[0-9][0-9]_*") if p.is_dir())
    assert folders == [slug for slug, _, _ in BIBLIA]


@pytest.mark.parametrize("slug,bpm,keyscale", BIBLIA)
def test_faixa_toml_matches_biblia(slug, bpm, keyscale):
    data = _toml(slug)
    assert data["bpm"] == bpm
    assert data["keyscale"] == keyscale
    assert f"{bpm} bpm" in data["prompt"]
    assert keyscale in data["prompt"]
    assert "no rap" in data["prompt"]
    assert data["seed"] == 42
    assert data["vocal_language"] == "en"
    assert data["lufs_target"] == -9.0


def test_pilot_track_loads_completely():
    faixa = load_faixa(CAELUM_ROOT / "01_quebra_de_fe")
    assert faixa.bpm == 100 and faixa.keyscale == "D minor"
    assert faixa.lyrics.startswith("[en]")


@pytest.mark.parametrize("slug", UNWRITTEN)
def test_unwritten_tracks_are_valid_except_template_lyrics(slug):
    # Prova que prompt/bpm/tipos do faixa.toml estao certos: a unica coisa que
    # falta e a letra em ingles (a recusa e a de letra de modelo).
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(CAELUM_ROOT / slug)


@pytest.mark.parametrize("slug", UNWRITTEN)
def test_unwritten_tracks_have_scene_context_in_letra_pt(slug):
    text = (CAELUM_ROOT / slug / "letra_pt.md").read_text(encoding="utf-8-sig")
    assert "Contexto da cena" in text
    assert "- ...\n" not in text.replace("\r\n", "\n").split("## Letra")[0]
    assert "[Verso 1]" in text and "[Ponte" in text


def test_unwritten_tracks_keep_the_template_files():
    for slug in UNWRITTEN:
        for name in ("letra_en.md", "pronuncia.md"):
            assert (CAELUM_ROOT / slug / name).is_file(), f"{slug}/{name} ausente"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: FAIL -- `test_album_has_exactly_the_ten_track_folders` (so existe a 01) e os demais com `FileNotFoundError`; `test_pilot_track_loads_completely` e o `01_quebra_de_fe` do `test_faixa_toml_matches_biblia` passam.

- [ ] **Step 3: Criar as 9 pastas com um script temporario**

Crie `scratchpad/make_faixas.py` (no scratchpad da sessao, nao no repo) com o conteudo abaixo e rode da raiz: `PYTHONPATH=. PYTHONUTF8=1 uv run python <scratchpad>/make_faixas.py`.

```python
import shutil
from pathlib import Path

ROOT = Path("caelum")
BASE = "melodic nu metal, downtuned 7-string guitars"

# slug, titulo, bpm, tom, duracao, prompt-resto, cena, monstro, voz, escala
FAIXAS = [
    ("02_executor", "Executor", 96, "A minor", 180.0,
     "stiff marching groove with dry tight snare, spoken-word verses, emotional clean male vocal in the chorus, short aggressive scream, no rap",
     "Caelum cumpre as ordens da Ordem Grave com orgulho; a primeira duvida aparece (flashback, antes da quebra de fe).",
     "monstro e o que a Ordem manda executar, sem perguntar por que.",
     "verso falado, refrao limpo, grito curto; o mantra 'Obey. Don't ask.' sussurrado.",
     "A menor; menor harmonica na voz da Ordem (mantra, pre-refrao), natural nos riffs."),
    ("03_silencio", "Silencio", 88, "E minor", 150.0,
     "sparse dark atmosphere, clean muted guitar passages, cold ambient textures, whispered verses, emotional clean male vocal, no screaming, no rap",
     "Caelum nota os sinais de que algo esta errado e escolhe nao ver, para nao perder a fe (flashback).",
     "o silencio dele alimenta o sistema que cria os monstros.",
     "sussurro e voz limpa, SEM grito; a faixa mais contida do album.",
     "E menor; menor harmonica nos trechos da Ordem, natural no resto."),
    ("04_a_mao_que_me_fez", "A mao que me fez", 108, "B minor", 180.0,
     "heavy, syncopated bouncy riffs, tight groove, emotional clean vocal alternating with aggressive scream in the chorus, breakdown, no rap",
     "Caelum sente raiva da Ordem que o formou e usou.",
     "a mao que cria os monstros e a que mais merece o nome.",
     "refrao alterna voz limpa e grito; breakdown antes do refrao final.",
     "B menor natural (raiva); sem harmonica."),
    ("05_culpa", "Culpa", 92, "F# minor", 180.0,
     "heavy sludgy, very downtuned, slow crushing groove, dirty distorted bass, clean vocal alternating with scream in the verses, no rap",
     "Cada 'monstro' que Caelum executou tinha um rosto; a culpa pesa.",
     "os 'monstros' eram gente e criaturas com rosto, vitimas da Ordem.",
     "voz limpa e grito alternados ja nos versos; a faixa mais suja.",
     "F# menor natural; sem harmonica."),
    ("06_revolta", "Revolta", 120, "C# minor", 180.0,
     "aggressive, fast, driving drums, shouted gang vocals, strong scream, brutal breakdown before the final chorus, no rap",
     "Caelum rompe com a Ordem; ponto mais distante de casa no plano de tons.",
     "ele ja e chamado de monstro por quem fica.",
     "gang vocals e grito forte; breakdown seco antes do refrao final.",
     "C# menor natural; a faixa mais rapida (120 bpm)."),
    ("07_do_outro_lado", "Do outro lado", 112, "F# minor", 180.0,
     "anthemic, big singalong chorus with gang choir vocals, breakdown, emotional clean male lead, no rap",
     "Caelum decide lutar contra a Ordem e se alia aos monstros que ela criou.",
     "escolhe ficar com os chamados monstros.",
     "coro (os monstros) no refrao grande e cantavel; lider limpo.",
     "F# menor natural; comeca a volta por quartas."),
    ("08_monstros", "Monstros", 98, "B minor", 180.0,
     "electronic textures, big emotional clean chorus, melodic and hopeful, restrained scream, no rap",
     "Caelum ve o mundo pelos olhos dos monstros, nao mais da Ordem. Centro do album.",
     "VIRADA: o rotulo se inverte; o verdadeiro monstro e quem controla o sistema.",
     "refrao limpo, o mais importante do album; mantra invertido 'Ask. Don't obey.'.",
     "B menor; menor melodica no refrao (6a e 7a elevadas subindo) e no mantra invertido."),
    ("09_fora_do_sistema", "Fora do sistema", 104, "E minor", 180.0,
     "cold electronic glitch textures, spoken-word verses, emotional clean male vocal in the chorus, short scream, no rap",
     "Caelum e discriminado e julgado por quem ainda vive dentro do sistema.",
     "quem esta dentro o chama de monstro; ele sabe quem e o monstro de verdade.",
     "verso falado, refrao limpo, grito curto; o sistema como textura eletronica fria.",
     "E menor natural nos riffs; melodica nas melodias de refrao."),
    ("10_caelum", "Caelum", 100, "D minor", 180.0,
     "heavy groove, huge emotional clean chorus, final powerful scream, cathartic, no rap",
     "Faixa-titulo: quem Caelum se tornou, vivendo como pessoa alternativa fora do sistema, julgado e assumido. Fecha o circulo: volta ao tom e BPM da faixa 01.",
     "assume o rotulo sem aceitar o significado.",
     "refrao limpo gigante, grito final; mantra invertido.",
     "D menor, mesmo tom da 01 (la, o sistema; aqui, o proprio Caelum); melodica no refrao."),
]

for slug, titulo, bpm, tom, dur, resto, cena, monstro, voz, escala in FAIXAS:
    dest = ROOT / slug
    assert not dest.exists(), f"{dest} ja existe"
    shutil.copytree(ROOT / "_modelo", dest)
    prompt = f"{BASE}, {resto}, {bpm} bpm, {tom}"
    (dest / "faixa.toml").write_text(
        "# Configuracao da faixa. So 'prompt' e obrigatorio.\n"
        "# Chaves desconhecidas sao erro (evita typo silencioso).\n"
        f'prompt = "{prompt}"\n'
        f"duration = {dur}       # segundos\n"
        "seed = 42\n"
        f"bpm = {bpm}\n"
        f'keyscale = "{tom}"\n'
        'vocal_language = "en"\n'
        "lufs_target = -9.0\n",
        encoding="utf-8",
    )
    (dest / "letra_pt.md").write_text(
        f"# {titulo} -- letra em portugues (fonte da verdade)\n\n"
        "Contexto da cena (o que acontece, o que Caelum sente):\n\n"
        f"- {cena}\n"
        f"- 'Monstro' aqui quer dizer: {monstro}\n"
        f"- Voz: {voz}\n"
        f"- Tom e escala: {tom} -- {escala}\n\n"
        "## Letra\n\n"
        "[Verso 1]\n...\n\n"
        "[Refrao -- limpo, melodico]\n...\n\n"
        "[Ponte -- gritada]\n...\n",
        encoding="utf-8",
    )
print("ok:", [f[0] for f in FAIXAS])
```

Expected: imprime `ok: ['02_executor', ..., '10_caelum']`; cada pasta tem os 4 arquivos (`letra_en.md` e `pronuncia.md` copiados do modelo). Se o script falhar no meio, apague so as pastas que ele criou (`caelum/02_*` a `caelum/10_*` que ainda tenham `letra_en.md` igual ao modelo) e rode de novo; nunca toque em `caelum/01_quebra_de_fe/`.

- [ ] **Step 4: Rodar e ver passar**

Run: `uv run pytest tests/test_caelum_biblia.py -v`
Expected: todos passam (1 de pastas + 10 de toml + 1 da 01 + 9 + 9 + 1). Se `test_unwritten_tracks_are_valid_except_template_lyrics` falhar com outra mensagem que nao `modelo`, o `faixa.toml` daquela faixa esta invalido: corrija o `faixa.toml` (nao o teste).

- [ ] **Step 5: Suite completa**

Run: `uv run pytest -q`
Expected: so as 8 falhas ja conhecidas; nenhuma nova.

- [ ] **Step 6: Commit**

```bash
git add tests/test_caelum_biblia.py caelum/02_executor caelum/03_silencio caelum/04_a_mao_que_me_fez caelum/05_culpa caelum/06_revolta caelum/07_do_outro_lado caelum/08_monstros caelum/09_fora_do_sistema caelum/10_caelum
git commit -m "$(cat <<'EOF'
feat: pastas das faixas 02-10 do album Caelum (faixa.toml e contexto da cena)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `caelum/BIBLIA.md` e README

**Files:**
- Create: `caelum/BIBLIA.md`
- Modify: `caelum/README.md` (um paragrafo no topo)
- Modify: `tests/test_caelum_biblia.py` (um teste novo no fim)

**Interfaces:**
- Consumes: `BIBLIA` e `CAELUM_ROOT` de `tests/test_caelum_biblia.py` / `caelum.faixa` (Task 2).
- Produces: documento de referencia; nada depende dele em codigo.

- [ ] **Step 1: Escrever o teste que falha**

Acrescente no fim de `tests/test_caelum_biblia.py`:

```python
def test_biblia_document_covers_every_track_and_the_two_axes():
    text = (CAELUM_ROOT / "BIBLIA.md").read_text(encoding="utf-8-sig")
    for slug, bpm, keyscale in BIBLIA:
        assert slug in text, f"{slug} nao aparece na biblia"
        assert f"{bpm}" in text and keyscale.replace(" minor", " menor") in text
    assert "executor" in text.lower()
    assert "quem e o monstro" in text.lower()
    assert "Obey. Don't ask." in text and "Ask. Don't obey." in text
    assert "ReaAssist" in text
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/test_caelum_biblia.py::test_biblia_document_covers_every_track_and_the_two_axes -q`
Expected: FAIL (`FileNotFoundError: ... BIBLIA.md`).

- [ ] **Step 3: Escrever `caelum/BIBLIA.md`**

Crie `caelum/BIBLIA.md` com exatamente este conteudo:

````markdown
# Caelum -- biblia do album 1

Spec: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md`.
Como usar as pastas: `caelum/README.md`.

## Conceito

**Caelum e um executor da Ordem Grave.** O executor medieval cumpria ordens
sem questionar; Caelum e a analogia de quem vive dentro de um sistema
fazendo o que mandam sem perguntar por que. O album conta o dia em que ele
pergunta, o que isso custa e a vida que escolhe depois: sair do sistema e
viver como acredita ser o certo, sendo julgado por quem ainda vive dentro
dele.

Dois eixos em todas as faixas:

1. **Obediencia sem questionar** (o executor).
2. **Quem e o monstro.** O sistema chama de "monstro" quem esta fora dele
   (as criaturas que a Ordem fabrica e, no fim, o proprio Caelum). A virada:
   os verdadeiros monstros sao quem controla o sistema. Aparecem nas letras
   como "voces"/"eles", sem rosto fixo.

**Final (album 1): caminho do meio.** A Ordem continua de pe; Caelum vive
livre fora dela, com os monstros que ela criou, e aceita ser julgado. A
historia segue num album 2.

Genero: nu metal melodico, vocal limpo + grito, sem rap, uma voz so
(Caelum, primeira pessoa), sem narrador.

## Arco e faixas

As faixas 02-03 sao flashback (a 01 abre pelo ponto de virada).

| Ato | # | Pasta | Cena | "Monstro" quer dizer |
|---|---|---|---|---|
| Fe | 01 | `01_quebra_de_fe` (pronta) | Descobre que a Ordem cria os monstros que executava | Os monstros eram obra da Ordem |
| | 02 | `02_executor` | Orgulho de cumprir ordens; a primeira duvida | O que a Ordem manda executar |
| | 03 | `03_silencio` | Ignora os sinais para nao perder a fe | O silencio dele alimenta o sistema |
| Ruptura | 04 | `04_a_mao_que_me_fez` | Raiva contra a Ordem que o formou | A mao que cria merece o nome |
| | 05 | `05_culpa` | Cada monstro executado tinha um rosto | Os "monstros" tinham rosto |
| | 06 | `06_revolta` | Rompe com a Ordem | Ja e chamado de monstro |
| | 07 | `07_do_outro_lado` | Luta contra a Ordem, aliado aos monstros | Escolhe ficar com eles |
| Nova realidade | 08 | `08_monstros` | Ve o mundo pelos olhos dos monstros | **Virada:** o monstro e quem controla o sistema |
| | 09 | `09_fora_do_sistema` | E discriminado por quem vive dentro | Quem esta dentro o chama de monstro |
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
| 05 | F# menor | 92 | Muito pesado | Limpo e grito alternados; a mais suja |
| 06 | C# menor | 120 | O mais rapido | Gang vocals, grito forte; breakdown |
| 07 | F# menor | 112 | Pesado, anthem | Coro (os monstros), refrao grande |
| 08 | B menor | 98 | Medio | Refrao limpo, o mais importante; mantra invertido |
| 09 | E menor | 104 | Medio | Verso falado, refrao limpo, grito curto |
| 10 | D menor | 100 | Medio a pesado | Refrao gigante, grito final; volta ao tom/BPM da 01 |

Valores sao pontos de partida; ajuste de ouvido na geracao.

### Escalas

- **Menor natural:** base dos riffs de todas as faixas.
- **Menor harmonica (7a elevada):** a voz da Ordem (mantra, pre-refrao e ponte nas faixas 01-03).
- **Menor melodica (6a e 7a elevadas, subindo):** melodias de refrao do ato 3; esperanca; mantra invertido.

O ACE-Step so recebe o tom (`keyscale`) e nao distingue harmonica de
melodica; isso fica na melodia que voce grava e na camada REAPER.

### Motivos

- **Mantra da Ordem:** "Obey. Don't ask." sussurrado/monotono nas faixas
  01-03; invertido, "Ask. Don't obey.", nas 08-10. Gravado com a sua voz no
  REAPER.
- **Curva do grito:** nenhum na 03, maximo nas 05 e 06, contido nas 08-10.
- **Breakdown** nas faixas 04, 06 e 07.
- **Linguagem do genero:** frases curtas e diretas, confessionais; ganchos
  repetidos; contraste verso falado, refrao aberto, grito na ponte.

## Producao hibrida

**Camada 1 -- ACE-Step (Kaggle):** banda (bateria, baixo, guitarras de 7
cordas), estrutura, groove, peso do refrao e vocal guia; Demucs separa os
stems.

**Camada 2 -- REAPER:** mantra da Ordem, texturas e transicoes (glitches,
risers, pads frios, impactos), scratches/samples (se voce tiver ou gravar),
tratamento da voz (grito, dobros, efeitos por ato) e edicoes (breakdown,
ganchos repetidos).

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
Voce pode instalar e usar por conta propria.

## Fichas das faixas

Cada pasta `caelum/NN_slug/` tem `faixa.toml` (prompt, BPM, tom) e
`letra_pt.md` com o contexto da cena. `letra_en.md` e `pronuncia.md` das
faixas 02-10 sao feitos na producao de cada uma (o `caelum_gerar` recusa
gerar enquanto a `letra_en.md` for o modelo).

Camada REAPER por faixa ([MCP] = ja da para fazer com as ferramentas
atuais; [manual] = no REAPER, por enquanto):

| # | Camada REAPER |
|---|---|
| 01 | Mantra sussurrado ao fundo do verso [MCP: faixa + FX; posicionar: manual] |
| 02 | Mantra falado; textura seca de "marcha" [manual] |
| 03 | Texturas frias e silencios [manual]; reverb/delay na voz [MCP] |
| 04 | Breakdown: corte/repeticao de trecho [manual] |
| 05 | Saturacao extra no baixo e na voz [MCP: FX] |
| 06 | Breakdown seco antes do refrao final [manual]; gang vocals dobrados [MCP] |
| 07 | Coro de vozes empilhadas no refrao [MCP: faixas + pan] |
| 08 | Mantra invertido "Ask. Don't obey." (sua voz, melodica) [MCP + manual] |
| 09 | Texturas eletronicas frias / glitches [manual] |
| 10 | Mantra invertido + camada final de coro; master [MCP: apply_master] |
````

- [ ] **Step 4: Apontar o README para a biblia**

Em `caelum/README.md`, logo depois da linha `` `docs/superpowers/specs/2026-10-02-caelum-album-design.md`. `` (fim do primeiro paragrafo), acrescente:

```markdown

Biblia do album (arco das 10 faixas, plano sonoro, camada REAPER):
`BIBLIA.md` (spec: `docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md`).
```

- [ ] **Step 5: Rodar e ver passar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: todos passam.

- [ ] **Step 6: Suite completa**

Run: `uv run pytest -q`
Expected: so as 8 falhas ja conhecidas; nenhuma nova.

- [ ] **Step 7: Commit**

```bash
git add caelum/BIBLIA.md caelum/README.md tests/test_caelum_biblia.py
git commit -m "$(cat <<'EOF'
docs: caelum/BIBLIA.md com arco, plano sonoro e producao hibrida do album

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```
