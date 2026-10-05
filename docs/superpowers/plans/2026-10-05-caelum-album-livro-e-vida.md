# Caelum "o livro e a vida" (21 faixas) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preparar o repositorio para o album de 21 faixas (10 pares V+M e Obedecer): 10 pastas novas das faixas M (o livro de Caelum, nu metal sinfonico), a biblia do livro (`caelum/livro.md`) com a ordem do disco, e os testes que travam tudo isso.

**Architecture:** Nenhum codigo de producao muda: `caelum/faixa.py` e `caelum/gerar.py` ja aceitam qualquer pasta sob `caelum/` (`resolve_faixa_dir`) e o `.gitignore` ja cobre `caelum/*/saida/`. O trabalho e (1) estender `tests/test_caelum_biblia.py` para conhecer as faixas M e a ordem do disco, (2) criar as 10 pastas M a partir do modelo, (3) escrever `caelum/livro.md`. As faixas V NAO sao renomeadas (evita travar o REAPER e quebrar caminhos em `songs.db`); as faixas M usam o prefixo `mNN_`.

**Tech Stack:** Python 3 (uv), pytest, TOML (`tomllib`), arquivos Markdown.

**Spec:** `docs/superpowers/specs/2026-10-05-caelum-album-livro-e-vida-design.md` (le tambem `2026-10-04-caelum-album-vida-real-design.md` e `2026-10-03-caelum-album-biblia-design.md`, de onde vem o arco de Caelum).

## Global Constraints

- Branch `caelum-album-piloto` (nao e worktree). **Nao fazer merge nem push** (decisao do autor: merge unico depois da gravacao).
- Pastas V existentes (`01_sozinho` ... `11_obedecer`) **nao sao renomeadas nem alteradas**.
- Pastas M: `m01_quebra_de_fe`, `m02_executor`, `m03_silencio`, `m04_a_mao_que_me_fez`, `m05_culpa`, `m06_revolta`, `m07_do_outro_lado`, `m08_monstros`, `m09_fora_do_sistema`, `m10_caelum` (minusculas, ASCII, sem acento).
- Cada `faixa.toml` de M: `seed = 42`, `vocal_language = "en"`, `lufs_target = -9.0`, `duration = "auto"`, prompt com `"{bpm} bpm"`, o tom (`keyscale`) e `"no rap"`.
- Tons/bpm das M (plano da biblia de 2026-10-03): M01 D minor 100, M02 A minor 96, M03 E minor 88, M04 B minor 108, M05 F# minor 92, M06 C# minor 120, M07 F# minor 112, M08 B minor 98, M09 E minor 104, M10 D minor 100.
- Ordem do disco (21): `01_sozinho`, `m01_quebra_de_fe`, `02_rotina`, `11_obedecer`, `m02_executor`, `03_o_que_nao_veio`, `m03_silencio`, `04_barulho`, `m04_a_mao_que_me_fez`, `05_vazio`, `m05_culpa`, `06_tempo_perdido`, `m06_revolta`, `07_silencio`, `m07_do_outro_lado`, `08_recomeco`, `m08_monstros`, `09_tarde_demais`, `m09_fora_do_sistema`, `10_caelum`, `m10_caelum`.
- O vocabulario da alegoria medieval (`FORBIDDEN_TERMS` em `tests/test_caelum_biblia.py`) continua proibido nas faixas V, em `conceito.md` e em `README.md`. Ele so e permitido nas pastas `mNN_*` e em `caelum/livro.md`.
- Textos do repositorio em portugues sem acentos (estilo dos arquivos existentes); arquivos lidos com `encoding="utf-8-sig"` nos testes.
- Commits terminam com a linha `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Fora deste plano:** letras PT/EN, pronuncia, geracao no ACE-Step, gravacao e mix das faixas M, e a refeita da Obedecer. Cada uma e um ciclo proprio, uma faixa por vez, comecando pelo **piloto da M01 (Quebra de fe)** para testar se o ACE-Step entrega som sinfonico.

## Review Focus

- Pasta M nova com `letra_en.md` ainda de modelo: `caelum_gerar` deve recusar antes de gastar uma geracao (coberto por `test_unwritten_tracks_are_valid_except_template_lyrics`, que passa a incluir as 10 M).
- `resolve_faixa_dir("m01_quebra_de_fe")` tem de achar a pasta (Task 1, `test_m_folders_resolve_by_slug`).
- Audio gerado em `caelum/mNN_*/saida/` nao pode entrar no git (Task 1, `test_m_saida_is_gitignored`).
- A excecao do vocabulario medieval nao pode vazar para as faixas V, `conceito.md` e `README.md` (Task 1, `test_scan_actually_covers_biblia_readme_and_tracks`).
- Pares 3 e 7: M03 e E/88 e M07 e F#/112, diferentes das V3 (E/112) e V7 (E/88) de proposito (Task 1, linhas de `M_FAIXAS`).

---

### Task 1: Testes que conhecem as faixas M e a ordem do disco

**Files:**
- Modify: `tests/test_caelum_biblia.py`

**Interfaces:**
- Consumes: `caelum.faixa.CAELUM_ROOT`, `FaixaError`, `load_faixa`; `caelum.gerar.resolve_faixa_dir`.
- Produces: constantes `V_FAIXAS`, `M_FAIXAS`, `BIBLIA` (= V + M), `ORDEM_DO_DISCO`, `M_ATO_KEYWORD`; helper `_is_allegory_allowed(rel)`. As Tasks 2 e 3 fazem estes testes passarem.

- [ ] **Step 1: Trocar o bloco `BIBLIA`/`UNWRITTEN` (linhas 1-30) por V, M, ordem do disco e `UNWRITTEN` com as M**

Substituir do inicio do arquivo ate o fim da lista `UNWRITTEN` (a linha `]` na 29) por:

```python
"""Trava as pastas do album contra a tabela da biblia e o conceito da vida real
(docs/superpowers/specs/2026-10-04-caelum-album-vida-real-design.md) e do livro
de Caelum (docs/superpowers/specs/2026-10-05-caelum-album-livro-e-vida-design.md)."""

import re
import subprocess
import tomllib

import pytest

from caelum.faixa import CAELUM_ROOT, FaixaError, load_faixa
from caelum.gerar import resolve_faixa_dir

# (slug, bpm, keyscale) -- fonte da verdade: tabela do plano/biblia.
# V = a vida real do autor (nu metal).
V_FAIXAS = [
    ("01_sozinho", 100, "D minor"),
    ("02_rotina", 96, "A minor"),
    ("03_o_que_nao_veio", 112, "E minor"),
    ("04_barulho", 108, "B minor"),
    ("05_vazio", 92, "F# minor"),
    ("06_tempo_perdido", 120, "C# minor"),
    ("07_silencio", 88, "E minor"),
    ("08_recomeco", 98, "B minor"),
    ("09_tarde_demais", 104, "E minor"),
    ("10_caelum", 100, "D minor"),
    ("11_obedecer", 96, "A minor"),
]

# M = o livro de Caelum (nu metal sinfonico), ver caelum/livro.md. Os pares 3 e
# 7 diferem de V no tom/bpm de proposito (M03 E/88, M07 F#/112).
M_FAIXAS = [
    ("m01_quebra_de_fe", 100, "D minor"),
    ("m02_executor", 96, "A minor"),
    ("m03_silencio", 88, "E minor"),
    ("m04_a_mao_que_me_fez", 108, "B minor"),
    ("m05_culpa", 92, "F# minor"),
    ("m06_revolta", 120, "C# minor"),
    ("m07_do_outro_lado", 112, "F# minor"),
    ("m08_monstros", 98, "B minor"),
    ("m09_fora_do_sistema", 104, "E minor"),
    ("m10_caelum", 100, "D minor"),
]

BIBLIA = V_FAIXAS + M_FAIXAS

# Ordem do disco: cada V seguida da M que a espelha; a 11 (Obedecer) entra antes
# do Executor.
ORDEM_DO_DISCO = [
    "01_sozinho", "m01_quebra_de_fe",
    "02_rotina", "11_obedecer", "m02_executor",
    "03_o_que_nao_veio", "m03_silencio",
    "04_barulho", "m04_a_mao_que_me_fez",
    "05_vazio", "m05_culpa",
    "06_tempo_perdido", "m06_revolta",
    "07_silencio", "m07_do_outro_lado",
    "08_recomeco", "m08_monstros",
    "09_tarde_demais", "m09_fora_do_sistema",
    "10_caelum", "m10_caelum",
]

# Palavra da orquestra do ato que tem de aparecer no prompt de cada M.
M_ATO_KEYWORD = {
    "m01_quebra_de_fe": "pipe organ",
    "m02_executor": "pipe organ",
    "m03_silencio": "pipe organ",
    "m04_a_mao_que_me_fez": "tremolo strings",
    "m05_culpa": "tremolo strings",
    "m06_revolta": "tremolo strings",
    "m07_do_outro_lado": "tremolo strings",
    "m08_monstros": "soaring strings",
    "m09_fora_do_sistema": "soaring strings",
    "m10_caelum": "soaring strings",
}

# Faixas cuja letra_en.md ainda e o modelo. Quando terminar a letra_en.md de
# uma faixa, remova o slug desta lista: ela passa a ser checada por load_faixa
# completo (test_written_tracks_load_completely).
UNWRITTEN = [
    "m01_quebra_de_fe",
    "m02_executor",
    "m03_silencio",
    "m04_a_mao_que_me_fez",
    "m05_culpa",
    "m06_revolta",
    "m07_do_outro_lado",
    "m08_monstros",
    "m09_fora_do_sistema",
    "m10_caelum",
]
```

- [ ] **Step 2: Trocar `test_album_has_exactly_the_track_folders` e apontar o teste do conceito so para as V**

Substituir `test_album_has_exactly_the_track_folders` por:

```python
def test_album_has_exactly_the_track_folders():
    folders = sorted(
        p.name for p in CAELUM_ROOT.iterdir()
        if p.is_dir() and re.match(r"m?\d\d_", p.name)
    )
    assert folders == sorted(slug for slug, _, _ in BIBLIA)
```

Em `test_biblia_document_covers_every_track_and_the_real_life_concept`, trocar `for slug, bpm, keyscale in BIBLIA:` por `for slug, bpm, keyscale in V_FAIXAS:` (as M nao estao na tabela do `conceito.md`; elas ficam no `livro.md`).

- [ ] **Step 3: Acrescentar os testes das faixas M e da ordem do disco**

Logo depois de `test_unwritten_tracks_keep_the_template_files`, acrescentar:

```python
@pytest.mark.parametrize("slug,keyword", sorted(M_ATO_KEYWORD.items()))
def test_m_prompt_is_symphonic_with_the_act_orchestra(slug, keyword):
    prompt = _toml(slug)["prompt"]
    assert "symphonic nu metal" in prompt
    assert keyword in prompt
    assert "DJ scratches" not in prompt


@pytest.mark.parametrize("slug", [slug for slug, _, _ in V_FAIXAS])
def test_v_prompts_stay_without_orchestra(slug):
    assert "symphonic" not in _toml(slug)["prompt"]


@pytest.mark.parametrize("slug", [slug for slug, _, _ in M_FAIXAS])
def test_m_scene_context_names_the_monster_and_the_mirror(slug):
    text = (CAELUM_ROOT / slug / "letra_pt.md").read_text(encoding="utf-8-sig")
    assert "- Monstro quer dizer: " in text
    assert "- Espelho (V): " in text


def test_m_pairs_3_and_7_differ_from_v_on_purpose():
    by_slug = {slug: (bpm, key) for slug, bpm, key in BIBLIA}
    assert by_slug["03_o_que_nao_veio"] == (112, "E minor")
    assert by_slug["m03_silencio"] == (88, "E minor")
    assert by_slug["07_silencio"] == (88, "E minor")
    assert by_slug["m07_do_outro_lado"] == (112, "F# minor")


def test_disc_order_is_the_21_tracks_with_obedecer_before_the_executor():
    assert len(ORDEM_DO_DISCO) == 21
    assert sorted(ORDEM_DO_DISCO) == sorted(slug for slug, _, _ in BIBLIA)
    assert ORDEM_DO_DISCO[0] == "01_sozinho" and ORDEM_DO_DISCO[-1] == "m10_caelum"
    i = ORDEM_DO_DISCO.index("11_obedecer")
    assert ORDEM_DO_DISCO[i - 1] == "02_rotina"
    assert ORDEM_DO_DISCO[i + 1] == "m02_executor"


def test_m_folders_resolve_by_slug():
    assert resolve_faixa_dir("m01_quebra_de_fe") == CAELUM_ROOT / "m01_quebra_de_fe"


def test_m_saida_is_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", "caelum/m01_quebra_de_fe/saida/1_master.wav"],
        cwd=CAELUM_ROOT.parent,
    )
    assert result.returncode == 0


def test_livro_lists_the_disc_order_and_the_story():
    text = (CAELUM_ROOT / "livro.md").read_text(encoding="utf-8-sig")
    positions = [text.find(f"`{slug}`") for slug in ORDEM_DO_DISCO]
    missing = [s for s, p in zip(ORDEM_DO_DISCO, positions) if p < 0]
    assert not missing, f"livro.md nao cita: {missing}"
    assert positions == sorted(positions), "livro.md: a tabela nao esta na ordem do disco"
    lowered = text.lower()
    for needle in (
        "assassin",
        "obey. don't ask.",
        "ask. don't obey.",
        "ordem grave",
        "2026-10-05-caelum-album-livro-e-vida-design.md",
    ):
        assert needle in lowered, f"livro.md nao menciona '{needle}'"


@pytest.mark.parametrize("name", ["conceito.md", "README.md"])
def test_conceito_and_readme_point_to_the_livro(name):
    assert "livro.md" in (CAELUM_ROOT / name).read_text(encoding="utf-8-sig")
```

- [ ] **Step 4: Isentar do varredor de vocabulario as pastas M e o `livro.md`**

Em `tests/test_caelum_biblia.py`, antes de `_album_text_files`, acrescentar:

```python
def _is_allegory_allowed(rel):
    """A alegoria medieval so e permitida no livro de Caelum (pastas mNN_* e livro.md)."""
    return rel.parts[0] == "livro.md" or re.match(r"m\d\d_", rel.parts[0]) is not None
```

Dentro de `_album_text_files`, logo depois do `if "saida" in rel.parts ...: continue`, acrescentar:

```python
        if _is_allegory_allowed(rel):
            continue
```

No fim de `test_scan_actually_covers_biblia_readme_and_tracks`, acrescentar:

```python
    assert "livro.md" not in scanned
    assert not any(re.match(r"m\d\d_", p) for p in scanned)
```

- [ ] **Step 5: Rodar e ver falhar**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: FAIL (muitos erros: pastas `m01_*` inexistentes, `livro.md` inexistente, `test_album_has_exactly_the_track_folders` diferente). Nenhum erro de importacao.

- [ ] **Step 6: Commit**

```bash
git add tests/test_caelum_biblia.py
git commit -m "test: biblia conhece as faixas M, a ordem do disco de 21 e o livro de Caelum" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Criar as 10 pastas das faixas M

**Files:**
- Create: `caelum/m01_quebra_de_fe/` ... `caelum/m10_caelum/` (cada uma com `faixa.toml`, `letra_pt.md`, `letra_en.md`, `pronuncia.md`)
- Test: `tests/test_caelum_biblia.py` (da Task 1)

**Interfaces:**
- Consumes: `M_FAIXAS`, `M_ATO_KEYWORD` e os testes da Task 1; os modelos `caelum/_modelo/letra_en.md` e `caelum/_modelo/pronuncia.md` (copiados sem alteracao).
- Produces: as 10 pastas M validas pelo `load_faixa` ate a `letra_en.md` (que e o modelo, entao `load_faixa` recusa com "modelo").

- [ ] **Step 1: Gerar as pastas com um script de uso unico (nao commitar o script)**

Run, a partir da raiz do repositorio (`C:\estudos\daw_music_studio`):

```bash
uv run python - <<'EOF'
import shutil
from pathlib import Path

root = Path("caelum")
modelo = root / "_modelo"

BASE = (
    "2000s nu metal, groove-driven, downtuned 7-string guitars with percussive syncopated "
    "palm-muted riffs, deep distorted bass, punchy hip-hop influenced drums, raw heavy production, "
    "symphonic nu metal with full orchestra and cinematic strings, in the style of early "
    "Linkin Park and Korn"
)
ATOS = {
    "fe": ("Fe", "solemn pipe organ, low liturgical choir, restrained strings"),
    "ruptura": ("Ruptura", "tremolo strings, brass stabs, timpani clashing with the distorted guitars"),
    "nova": ("Nova realidade", "open soaring strings, rising choir, hopeful orchestral swells"),
}

# (slug, n, titulo, ato, bpm, tom, peso/voz, cena, monstro, espelho)
FAIXAS = [
    ("m01_quebra_de_fe", "01", "Quebra de fe", "fe", 100, "D minor",
     "medium groove, dark atmospheric verses, emotional clean male vocal in the chorus, aggressive scream in the bridge",
     "Caelum, executor da Ordem Grave, descobre que a Ordem cria os monstros que ele executava",
     "os monstros eram obra da Ordem",
     "01 Sozinho: o autor acha o livro e fica sozinho com uma verdade que ninguem quer ouvir"),
    ("m02_executor", "02", "Executor", "fe", 96, "A minor",
     "marching groove with dry snare, spoken verses, emotional clean male vocal in the chorus, short scream",
     "orgulho de cumprir ordens sem perguntar; a primeira duvida",
     "monstro = o que a Ordem manda executar",
     "02 Rotina e 11 Obedecer: piloto automatico e obedecer calado"),
    ("m03_silencio", "03", "Silencio", "fe", 88, "E minor",
     "light and restrained, whispered then clean male vocal, no scream",
     "ignora os sinais para nao perder a fe",
     "o silencio dele alimenta o sistema",
     "03 Nunca foi lar: a casa que nao foi lar, a verdade que se evita"),
    ("m04_a_mao_que_me_fez", "04", "A mao que me fez", "ruptura", 108, "B minor",
     "heavy syncopated riff, clean male vocal alternating with screams in the chorus",
     "raiva contra a Ordem que o formou",
     "a mao que cria e a que merece o nome",
     "04 Barulho: subir a montanha contra a voz que diz que nao da"),
    ("m05_culpa", "05", "Culpa", "ruptura", 92, "F# minor",
     "very heavy and dragging, dirty low-end, clean male vocal alternating with screams",
     "cada monstro que executou tinha um rosto",
     "os monstros tinham rosto",
     "05 Vazio: o fundo, a agua que engole"),
    ("m06_revolta", "06", "Revolta", "ruptura", 120, "C# minor",
     "fastest and most aggressive, gang vocals, strong screams, breakdown before the final chorus",
     "rompe com a Ordem",
     "ele ja e chamado de monstro",
     "06 Tempo perdido: por que obedeci calado? a conta e minha"),
    ("m07_do_outro_lado", "07", "Do outro lado", "ruptura", 112, "F# minor",
     "heavy anthemic, big choir of voices in the chorus, clean male vocal",
     "decide lutar contra a Ordem e se alia aos monstros",
     "escolhe ficar com os chamados monstros",
     "07 Silencio: ser entendido por alguem; aqui, achar quem o entende"),
    ("m08_monstros", "08", "Monstros", "nova", 98, "B minor",
     "medium groove, bright memorable chorus, clean male vocal, controlled scream",
     "ve o mundo pelos olhos dos monstros, nao mais da Ordem (centro do livro)",
     "VIRADA: o rotulo se inverte; o monstro e quem controla o sistema",
     "08 Recomeco: a voz vira onda; aqui, o rotulo vira do avesso"),
    ("m09_fora_do_sistema", "09", "Fora do sistema", "nova", 104, "E minor",
     "medium groove, spoken verses, clean male vocal in the chorus, short scream, cold electronic touches",
     "e discriminado e julgado por quem vive dentro do sistema",
     "quem esta dentro o chama de monstro; ele sabe quem e",
     "09 Tarde demais: o medo do tempo; aqui, o julgamento de quem ficou"),
    ("m10_caelum", "10", "Caelum", "nova", 100, "D minor",
     "medium to heavy, giant chorus, band and orchestra playing together, final scream",
     "faixa-titulo: quem se tornou, vivendo fora do sistema, julgado; a historia do livro e a do autor se encontram",
     "assume o rotulo sem aceitar o significado",
     "10 Caelum: os passaros e o ceu; as duas historias se encontram"),
]

for slug, n, titulo, ato, bpm, tom, peso, cena, monstro, espelho in FAIXAS:
    pasta = root / slug
    pasta.mkdir()
    ato_nome, orq = ATOS[ato]
    prompt = f"{BASE}, {orq}, {peso}, no rap, {bpm} bpm, {tom}"
    assert '"' not in prompt
    (pasta / "faixa.toml").write_text(
        "# Configuracao da faixa. So 'prompt' e obrigatorio.\n"
        "# Chaves desconhecidas sao erro (evita typo silencioso).\n"
        f'prompt = "{prompt}"\n'
        'duration = "auto"       # automatica: o ACE-Step ajusta a duracao a letra\n'
        "seed = 42\n"
        f"bpm = {bpm}\n"
        f'keyscale = "{tom}"\n'
        'vocal_language = "en"\n'
        "lufs_target = -9.0\n",
        encoding="utf-8",
    )
    (pasta / "letra_pt.md").write_text(
        f"# {titulo} (M{n}) -- letra em portugues (fonte da verdade)\n\n"
        "Contexto da cena (o que acontece no livro, o que Caelum sente):\n\n"
        f"- Cena: {cena}\n"
        f"- Monstro quer dizer: {monstro}\n"
        f"- Espelho (V): {espelho}\n"
        f"- Ato: {ato_nome}; orquestra: {orq}\n"
        "- Letra por escrever: propor 3-4 imagens ao autor antes (poesia e metafora, nunca literal).\n\n"
        "## Letra\n\n"
        "[Verso 1]\n...\n\n"
        "[Refrao -- limpo, melodico]\n...\n\n"
        "[Ponte -- gritada]\n...\n",
        encoding="utf-8",
    )
    shutil.copy(modelo / "letra_en.md", pasta / "letra_en.md")
    shutil.copy(modelo / "pronuncia.md", pasta / "pronuncia.md")
    print("criada", pasta)
EOF
```

Expected: 10 linhas `criada caelum\mNN_...`.

- [ ] **Step 2: Rodar os testes das pastas**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: so falham `test_livro_lists_the_disc_order_and_the_story` e `test_conceito_and_readme_point_to_the_livro[...]` (o `livro.md` e o ponteiro sao da Task 3); tudo o mais passa.

- [ ] **Step 3: Conferir que nada de audio ou projeto entrou e commitar**

Run: `git status --short caelum`
Expected: so arquivos novos `caelum/mNN_*/{faixa.toml,letra_pt.md,letra_en.md,pronuncia.md}`.

```bash
git add caelum/m0*_* caelum/m10_caelum
git commit -m "feat: 10 pastas das faixas M (o livro de Caelum, nu metal sinfonico) com tom, bpm e contexto da cena" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Biblia do livro (`caelum/livro.md`) e ponteiros

**Files:**
- Create: `caelum/livro.md`
- Modify: `caelum/conceito.md` (uma frase no topo), `caelum/README.md` (uma frase e a contagem de pastas)
- Test: `tests/test_caelum_biblia.py` (da Task 1)

**Interfaces:**
- Consumes: `ORDEM_DO_DISCO` (os 21 slugs entre crases, na ordem do disco, devem aparecer em `livro.md` pela primeira vez na tabela da ordem do disco).
- Produces: `caelum/livro.md`, fonte da verdade da ordem do disco, do espelho V/M, do som sinfonico e do fluxo das faixas M.

- [ ] **Step 1: Criar `caelum/livro.md`**

Importante: os slugs entre crases so podem aparecer pela primeira vez na tabela "Ordem do disco" (nao os cite antes dela).

```markdown
# Caelum -- o livro e a vida (album de 21 faixas)

**Spec:** `docs/superpowers/specs/2026-10-05-caelum-album-livro-e-vida-design.md`. A vida real do
autor (faixas V) esta em `conceito.md` e no spec de 2026-10-04; o arco de Caelum (faixas M) vem da
biblia de 2026-10-03.

## A ideia (estilo Assassin's Creed)

O autor, hoje, encontra um livro antigo sobre Caelum, um executor medieval da **Ordem Grave**, e
transforma esse livro em musica. Duas historias que se espelham:

- **V (a vida):** a vida real do autor. Nu metal, sem orquestra. As 11 pastas `NN_*` (10 do arco +
  a 11, Obedecer).
- **M (o livro):** a historia de Caelum medieval, em primeira pessoa e sem narrador. Nu metal
  sinfonico: a mesma banda mais orquestra e coral. As 10 pastas `mNN_*`.

A voz e sempre a do autor. "Caelum" e o artista, o personagem do livro e o titulo das duas ultimas
faixas.

## Ordem do disco (21 faixas)

Cada V e seguida da M que espelha o mesmo sentimento; a 11 entra antes do Executor. V e M do mesmo
par usam o mesmo tom e bpm, **exceto nos pares 3 e 7** (V3 E/112 e V7 E/88; M3 E/88 e M7 F#/112).

| # | Pasta | Tipo | Titulo | Tom / bpm | O espelho |
|---|---|---|---|---|---|
| 1 | `01_sozinho` | V | Sozinho | D / 100 | Solidao; o autor acha o livro |
| 2 | `m01_quebra_de_fe` | M | Quebra de fe | D / 100 | A verdade que ninguem quer ouvir |
| 3 | `02_rotina` | V | Rotina | A / 96 | Moto todo dia, piloto automatico |
| 4 | `11_obedecer` | V | Obedecer | A / 96 | Obedecer calado (a faixa da igreja) |
| 5 | `m02_executor` | M | Executor | A / 96 | Cumprir ordens sem perguntar |
| 6 | `03_o_que_nao_veio` | V | Nunca foi lar | E / 112 | A casa que nao foi lar |
| 7 | `m03_silencio` | M | Silencio | E / 88 | Ignorar os sinais para nao perder a fe |
| 8 | `04_barulho` | V | Barulho | B / 108 | A montanha: eu nao morro aqui |
| 9 | `m04_a_mao_que_me_fez` | M | A mao que me fez | B / 108 | Raiva de quem o moldou |
| 10 | `05_vazio` | V | Vazio | F# / 92 | O afogamento |
| 11 | `m05_culpa` | M | Culpa | F# / 92 | Cada monstro tinha um rosto |
| 12 | `06_tempo_perdido` | V | Tempo perdido | C# / 120 | Por que obedeci calado? |
| 13 | `m06_revolta` | M | Revolta | C# / 120 | Rompe com a Ordem |
| 14 | `07_silencio` | V | Silencio (quem me entenda) | E / 88 | Ser entendido |
| 15 | `m07_do_outro_lado` | M | Do outro lado | F# / 112 | Os monstros que o entendem |
| 16 | `08_recomeco` | V | Recomeco | B / 98 | O vento leva a minha voz |
| 17 | `m08_monstros` | M | Monstros | B / 98 | A virada: o monstro e quem controla o sistema |
| 18 | `09_tarde_demais` | V | Tarde demais | E / 104 | As quatro estacoes |
| 19 | `m09_fora_do_sistema` | M | Fora do sistema | E / 104 | Ser julgado por quem ficou |
| 20 | `10_caelum` | V | Caelum | D / 100 | Os passaros e o ceu |
| 21 | `m10_caelum` | M | Caelum | D / 100 | As duas historias se encontram no ceu |

## A historia de Caelum no livro

Tres atos. Caelum e executor da Ordem Grave e cumpre ordens sem questionar. Descobre que a Igreja
fabrica os monstros que ele matava, rompe, se junta aos monstros e e julgado. Final do album 1:
caminho do meio (a Ordem continua de pe; Caelum vive livre fora dela).

| Ato | Faixas M | Cena | "Monstro" quer dizer |
|---|---|---|---|
| Fe | M01-M03 | Descobre a verdade; orgulho de executar; ignora os sinais | Obra da Ordem; o que a Ordem manda executar |
| Ruptura | M04-M07 | Raiva, culpa, rompimento, alianca com os monstros | A mao que cria merece o nome; os monstros tinham rosto |
| Nova realidade | M08-M10 | A virada, o julgamento, o encontro com o ceu | O monstro e quem controla o sistema |

Dois eixos: **obediencia sem questionar** e **quem e o monstro**. Mantra da Ordem: **"Obey. Don't
ask."** sussurrado nas M01-M03, **invertido** ("Ask. Don't obey.") nas M08-M10; gravado com a voz do
autor na camada REAPER.

## Som

**V:** guitarras de 7 cordas afinadas baixo, verso baixo, refrao limpo, grito quando o sentimento
pede; sem orquestra.

**M:** a mesma banda mais orquestra. O prompt de cada M diz "symphonic nu metal" e a orquestra do ato:

| Ato | Orquestra (palavras do prompt) | Sensacao |
|---|---|---|
| Fe | pipe organ, low liturgical choir, restrained strings | O som da Ordem: solene, frio, menor harmonica |
| Ruptura | tremolo strings, brass stabs, timpani | A orquestra vira ameaca e depois se rompe |
| Nova realidade | open soaring strings, rising choir | O som da Ordem volta transformado em saida e esperanca |

Cada M abre com som de livro (folha, pena na tinta); a V nao. Na faixa final (`m10_caelum`, a 21),
a banda do V e a orquestra do M tocam juntas.

**Limite:** o ACE-Step ainda nao foi testado com orquestra. Antes de escrever as outras 9 letras M,
gerar so a M01 (Quebra de fe) em 3 ou 4 tentativas (seeds e variacoes de prompt); se o sinfonico nao
soar, ajustar o prompt e, se preciso, mover a orquestra para a camada REAPER (MIDI e instrumentos
virtuais, trabalho manual do autor).

## Fluxo de cada faixa M

1. Cena e imagem combinadas com o autor (propor 3-4 imagens com um verso de exemplo e recomendacao).
2. Letra PT (poetica, metaforica, uma imagem unica; fonte da verdade). 3. Aprovacao.
4. EN (silabas que cabem na melodia) + pronuncia em PT-BR; tirar o slug de `UNWRITTEN` em
   `tests/test_caelum_biblia.py`. 5. Testes. 6. Geracao: `uv run python scripts/caelum_gerar.py m01_quebra_de_fe`.
7. Stems depois, so se gostar. 8. O autor grava a voz e faz mix/master; merge unico na `main`
   depois (decisao dele).

## Regras

- Primeira pessoa, uma imagem unica por faixa, linhas curtas (ate 10 silabas), sem narrador.
- M e alegoria medieval: nada de pessoas, igrejas ou partidos reais; critica o MECANISMO de
  controle. V segue a guarda de abordagem de `conceito.md`.
- "Pegar a versao antiga e trabalhar em cima": mesma metrica, mesmo som, nada alem.
```

- [ ] **Step 2: Apontar `conceito.md` e `README.md` para o livro (sem vocabulario medieval)**

Em `caelum/conceito.md`, depois da linha `Como usar as pastas: \`caelum/README.md\`.` (linha 7), acrescentar uma linha:

```markdown
O album final tem 21 faixas (as daqui mais as do livro de Caelum, em sinfonico): ordem do disco e historia do livro em `caelum/livro.md`.
```

Em `caelum/README.md`, substituir `Pasta de trabalho do album (10 musicas), baseado na vida real do autor (um sentimento por faixa). Conceito atual:` por `Pasta de trabalho do album (21 faixas: as da vida real do autor, um sentimento por faixa, e as do livro de Caelum, em sinfonico; ordem do disco em \`livro.md\`). Conceito atual:` e, no paragrafo "Uma pasta por faixa", acrescentar ao fim da primeira frase: ` As dez pastas \`mNN_<slug>/\` do livro de Caelum seguem o mesmo formato (ver \`livro.md\`).`

Nao escrever "Ordem Grave", "executor" nem outros termos de `FORBIDDEN_TERMS` nesses dois arquivos.

- [ ] **Step 3: Rodar os testes do album**

Run: `uv run pytest tests/test_caelum_biblia.py -q`
Expected: todos passam.

- [ ] **Step 4: Rodar a suite completa do projeto**

Run: `uv run pytest -q`
Expected: tudo verde (a contagem de testes sobe em relacao a antes; reportar os numeros reais da saida). Se algo nao relacionado ao album falhar, parar e reportar.

- [ ] **Step 5: Commit**

```bash
git add caelum/livro.md caelum/conceito.md caelum/README.md
git commit -m "docs: livro.md (ordem do disco de 21, historia de Caelum, som sinfonico) e ponteiros" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

## Self-review (feito ao escrever)

- **Cobertura da spec:** estrutura de 21 faixas e ordem (Task 1 `ORDEM_DO_DISCO`, Task 3 tabela); pares 3 e 7 (Task 1 `test_m_pairs_3_and_7...`); som V sem orquestra e M sinfonico por ato (Task 1 testes de prompt, Task 2 prompts, Task 3 secao Som); mantra (Task 3); piloto M01 e riscos do ACE-Step (Task 3 secao Limite; execucao fora do plano); renomeacao de pastas decidida (nenhuma renomeacao: V intocadas, M prefixo `m`); fluxo e regras (Task 3). Letras M, geracao e gravacao: fora do escopo, declarado nas Global Constraints.
- **Placeholders:** nenhum; os `...` em `letra_pt.md` das M sao o modelo de letra por escrever, exigido pelos testes existentes (`[Verso 1]`, `[Ponte`).
- **Consistencia de nomes:** `V_FAIXAS`, `M_FAIXAS`, `BIBLIA`, `ORDEM_DO_DISCO`, `M_ATO_KEYWORD`, `_is_allegory_allowed` iguais entre Tasks; os 10 slugs M identicos em Constraints, Task 1, Task 2 e Task 3.
- **Prompt x teste:** cada prompt M contem `symphonic nu metal`, a orquestra do ato (`pipe organ` / `tremolo strings` / `soaring strings`), `no rap`, `"{bpm} bpm"` e o tom.
