# Caelum -- Album (frente 1: piloto) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deixar o repositorio pronto para produzir uma faixa do album Caelum de ponta a ponta (merge do kernel batch, pasta `caelum/`, comando de geracao por faixa, montador de sessao do REAPER) e rodar a faixa-piloto com o usuario.

**Architecture:** O pipeline existente (`ace_step.orchestrator.run_generation`: kernel batch no Kaggle = ACE-Step + Demucs) e reaproveitado sem reescrita. Uma camada fina em `caelum/` le a configuracao de cada faixa (`faixa.toml` + `letra_en.md`) e grava tudo na pasta da propria faixa. Um modulo novo em `reaper_bridge/` monta a sessao do REAPER (stems importados, vocal da IA silenciado, faixa `voz_caelum` armada), exposto como ferramenta MCP.

**Tech Stack:** Python 3.11+ (`tomllib`), pytest, reapy (REAPER), Kaggle API, SQLite (`ace_step/song_db.py`), `uv`.

**Spec:** `docs/superpowers/specs/2026-10-02-caelum-album-design.md`

## Global Constraints

- Estilo do album: nu metal melodico, vocal limpo + grito, **sem rap**; um unico cantor (o usuario, Caelum), em primeira pessoa; sem narrador.
- Letras finais em **ingles**; a fonte da verdade do significado e a letra em **portugues** (`letra_pt.md`); a adaptacao NAO e traducao literal.
- Cada faixa tem pasta propria `caelum/NN_<slug>/` com `letra_pt.md`, `letra_en.md`, `pronuncia.md`, `faixa.toml`; saidas geradas ficam em `caelum/NN_<slug>/saida/` e NAO sao versionadas (audio, stems, projetos do REAPER).
- `ace_step/lyrics.py` (letra via API do Claude) NAO e usado: as letras entram prontas via `lyrics=`.
- Separacao de stems: Demucs `htdemucs_6s` (vocals, drums, bass, guitar, piano, other), feita no proprio kernel batch.
- O vocal guia da IA e **guardado** como referencia (faixa `guia_ia`, silenciada), nunca entra na mixagem final.
- Testes automatizados no estilo do repositorio (`tests/fakes.py`, `unittest.mock.patch`, pytest); REAPER e Kaggle sempre mockados nos testes.
- Verificacao ao vivo no REAPER: **somente em faixas temporarias novas**, em projeto novo e vazio; nunca reordenar/deselecionar faixas existentes (efeitos colaterais conhecidos).
- Comandos Python rodam com `uv run` a partir da raiz `C:\estudos\daw_music_studio`. Texto de codigo/comentarios/commits no estilo do repo (portugues sem acentos em codigo de `ace_step/`; `reaper_bridge/` usa acentos).
- Commits terminam com a linha: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Fora do escopo: divulgacao, mix/master finais do album, biblia do album, as outras 9 faixas, checagem automatica de pronuncia, qualquer app/front-end.

## Review Focus

1. `faixa.toml` com chave desconhecida ou com typo (ex.: `bpn = 140`): deve falhar com mensagem clara, nao ser ignorado em silencio.
2. `letra_en.md` vazia (ou so espacos) / `prompt` vazio: nao pode chegar ao kernel e gastar uma geracao do Kaggle; deve falhar antes de criar a musica no banco.
3. Rodar `build_vocal_session` duas vezes na mesma sessao: nao pode duplicar faixas (`guia_ia`, `voz_caelum`, stems) nem mexer em faixas do usuario; deve falhar antes de qualquer mutacao.
4. Pasta de stems sem nenhum arquivo `<id>_stem_*.wav` (separacao falhou): erro claro, sem criar faixas. Pasta sem o stem `vocals` (plano B instrumental): funciona e simplesmente nao cria `guia_ia`.
5. Rodar `scripts/caelum_gerar.py` a partir de qualquer pasta / com cwd diferente da raiz: precisa achar os pacotes do repo e a pasta da faixa.

---

## Mapa de arquivos

| Arquivo | Acao | Responsabilidade |
|---|---|---|
| (git) merge de `worktree-ace-step-batch-kernel` | Task 0 | traz o kernel batch (sem ngrok) para a `master` |
| `.gitignore` | Modify (Task 1) | ignora saidas geradas de `caelum/` |
| `caelum/README.md` | Create (Task 1) | como usar a pasta, fluxo por faixa, convencoes |
| `caelum/_modelo/{faixa.toml,letra_pt.md,letra_en.md,pronuncia.md}` | Create (Task 1) | modelos copiados para cada faixa nova |
| `caelum/__init__.py` | Create (Task 2) | torna `caelum` importavel |
| `caelum/faixa.py` | Create (Task 2) | `Faixa`, `FaixaError`, `load_faixa`, `CAELUM_ROOT` |
| `tests/test_caelum_faixa.py` | Create (Task 2) | testes de `load_faixa` + do modelo |
| `caelum/gerar.py` | Create (Task 3) | `resolve_faixa_dir`, `gerar` |
| `scripts/caelum_gerar.py` | Create (Task 3) | CLI fino sobre `caelum.gerar` |
| `tests/test_caelum_gerar.py` | Create (Task 3) | testes de `gerar`/`resolve_faixa_dir` |
| `reaper_bridge/vocal_session.py` | Create (Task 4) | `build_vocal_session` |
| `tests/test_vocal_session.py` | Create (Task 4) | testes com `FakeProject` |
| `mcp_server.py` | Modify (Task 5) | tool `reaper_build_vocal_session` |
| `tests/test_mcp_server.py` | Modify (Task 5) | testes da tool |
| `caelum/01_<slug>/*` | Create (Task 7) | a faixa-piloto |

---

### Task 0: Passo zero -- mesclar o kernel batch na master

**Files:**
- Merge: branch `worktree-ace-step-batch-kernel` -> `master` (sem edicao manual de codigo, salvo conflitos)

**Interfaces:**
- Consumes: nada.
- Produces: `ace_step.orchestrator.run_generation(db_path, output_dir, song_id, *, prompt, duration, seed, bpm, keyscale, vocal_language, lufs_target, lyrics=None, timeout=2700.0, poll_interval=20.0) -> tuple[str, str | None]` (sem `base_url`/`api_key`); `ace_step.song_db.create_song/update_song/get_song`. As tasks 3 em diante dependem desta assinatura.

Contexto verificado em 2026-10-02: `git merge-tree --write-tree master worktree-ace-step-batch-kernel` nao reporta conflitos (merge limpo). A branch esta checada em `.claude/worktrees/ace-step-batch-kernel`; isso nao impede o merge na `master`. O working tree da `master` tem `.gitignore` modificado (linha `music21_test_output/`, do usuario) e arquivos nao rastreados (`README.md.docx`, `music-main/`).

- [ ] **Step 1: Confirmar o estado antes do merge**

Run:
```bash
git status --short && git branch --show-current && git merge-tree --write-tree --name-only master worktree-ace-step-batch-kernel
```
Expected: branch `master`; `git merge-tree` imprime so um hash de arvore (sem linhas `CONFLICT`). Se aparecer qualquer `CONFLICT`, PARE e reporte ao usuario antes de continuar.

- [ ] **Step 2: Rodar a suite da master ANTES do merge (linha de base)**

Run: `uv run pytest -q`
Expected: tudo verde. Anote o numero de testes (`N passed`) para comparar depois. Se algo ja falha na `master`, PARE e reporte (nao e culpa do merge).

- [ ] **Step 3: Mesclar**

Run:
```bash
git merge --no-ff worktree-ace-step-batch-kernel -m "$(cat <<'EOF'
merge: kernel batch do ace_step (sem ngrok) na master

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```
Expected: `Merge made by the 'ort' strategy`. Se recusar por causa do `.gitignore` modificado (`Your local changes ... would be overwritten`), rode `git stash push .gitignore`, repita o merge e depois `git stash pop`. Nao descarte a alteracao do usuario.

- [ ] **Step 4: Rodar a suite completa depois do merge**

Run: `uv run pytest -q`
Expected: tudo verde. O numero de testes muda (a branch remove os testes do proxy/cliente HTTP e adiciona os do kernel batch e do render) -- isso e esperado. Qualquer FALHA deve ser investigada (use `superpowers:systematic-debugging`) antes de seguir.

- [ ] **Step 5: Verificacao ao vivo -- geracao curta real (kernel batch no Kaggle)**

Este passo gasta cota do Kaggle e leva ate ~45 min (setup do kernel + geracao + separacao). Peca ao usuario para confirmar que pode rodar.

Run:
```bash
uv run python scripts/criar_musica.py --prompt "melodic nu metal, downtuned heavy guitars, clean chorus, aggressive scream, 120 bpm" --duration 30 --lyrics "[en]
[Verse]
I walked the road alone
[Chorus]
Now I am coming home" --db ace_step/output/smoke.db --timeout 2700
```
Expected: imprime `Musica #1 pronta: ace_step\output\1_master.wav`. Confirme que existem em `ace_step/output/`: `1_master.wav` e os seis `1_stem_{vocals,drums,bass,guitar,piano,other}.wav` (`ls ace_step/output/`). Se `criar_musica.py` falhar com `ModuleNotFoundError: No module named 'ace_step'`, rode a mesma linha como `uv run python -m scripts.criar_musica ...` e **avise o usuario** (os scripts antigos nao funcionam com `python scripts/x.py`; o `caelum_gerar.py` novo corrige isso por conta propria, os antigos ficam fora do escopo). Se a geracao falhar por razao do Kaggle (auth, cota), reporte a mensagem exata ao usuario.

- [ ] **Step 6: Registrar o resultado**

Nao ha arquivo para commitar (o merge ja e o commit). Reporte: `N passed` antes/depois, e o resultado do smoke ao vivo (quais arquivos foram gerados). `ace_step/output/` ja e ignorado pelo git.

---

### Task 1: Estrutura `caelum/` (gitignore, README, modelos)

**Files:**
- Modify: `.gitignore`
- Create: `caelum/README.md`
- Create: `caelum/_modelo/faixa.toml`, `caelum/_modelo/letra_pt.md`, `caelum/_modelo/letra_en.md`, `caelum/_modelo/pronuncia.md`

**Interfaces:**
- Consumes: nada.
- Produces: o formato de `faixa.toml` (chaves `prompt`, `duration`, `seed`, `bpm`, `keyscale`, `vocal_language`, `lufs_target`) e a convencao de que `letra_en.md` e enviado **inteiro** ao ACE-Step. A Task 2 le esses arquivos.

- [ ] **Step 1: Ignorar saidas geradas**

Em `.gitignore`, logo depois do bloco `ace_step/output/` / `music21_test_output/`, acrescente:

```gitignore

# Album Caelum: audio, stems, bancos e projetos do REAPER gerados por faixa
caelum/*/saida/
caelum/*/*.rpp
caelum/*/*.rpp-bak
caelum/*/*.reapeaks
```

(Se a linha `music21_test_output/` ja estiver no arquivo como alteracao local do usuario, mantenha-a e inclua-a neste commit.)

- [ ] **Step 2: Criar o modelo de `faixa.toml`**

`caelum/_modelo/faixa.toml`:
```toml
# Configuracao da faixa. So 'prompt' e obrigatorio.
# Chaves desconhecidas sao erro (evita typo silencioso).
prompt = "melodic nu metal, downtuned 7-string guitars, heavy groove, emotional clean male vocal in the chorus, aggressive scream in the bridge, no rap, 120 bpm"
duration = 180.0       # segundos
seed = 42
bpm = 120              # opcional
# keyscale = "D minor" # opcional
vocal_language = "en"
lufs_target = -9.0
```

- [ ] **Step 3: Criar os modelos de letra e pronuncia**

Em todos os blocos de arquivo deste step, o conteudo do arquivo e **so o que esta dentro do bloco**, sem as cercas ``` (principalmente em `letra_en.md`, que comeca na linha `[en]`).

`caelum/_modelo/letra_pt.md`:
```markdown
# <Titulo da faixa> -- letra em portugues (fonte da verdade)

Contexto da cena (o que acontece, o que Caelum sente):

- ...

## Letra

[Verso 1]
...

[Refrao -- limpo, melodico]
...

[Ponte -- gritada]
...
```

`caelum/_modelo/letra_en.md` (este arquivo e enviado INTEIRO ao ACE-Step -- nao coloque comentarios nele):
```text
[en]
[Verse]
(write the English lyrics here)
[Chorus]
(write the chorus here)
[Bridge]
(write the bridge here)
```

`caelum/_modelo/pronuncia.md`:
```markdown
# <Titulo da faixa> -- folha de pronuncia

Legenda: pronuncia escrita em portugues; **negrito** = silaba tonica; (!) = palavra dificil.

| Linha em ingles | Pronuncia (PT-BR) | Observacoes |
|---|---|---|
| ... | ... | ... |

## Palavras dificeis (th, -ed final, r, h, vogais curtas/longas)

- ...
```

- [ ] **Step 4: Criar `caelum/README.md`**

```markdown
# Caelum -- album de nu metal

Pasta de trabalho do album (10 musicas). Design:
`docs/superpowers/specs/2026-10-02-caelum-album-design.md`.

## Uma pasta por faixa

Copie `_modelo/` para `NN_<slug>/` (ex.: `01_semente/`). Cada faixa tem:

- `letra_pt.md` -- fonte da verdade (significado e emocao)
- `letra_en.md` -- adaptacao para ingles, enviada INTEIRA ao ACE-Step (sem comentarios)
- `pronuncia.md` -- folha de pronuncia linha a linha
- `faixa.toml` -- prompt de estilo, bpm, tom, seed, duracao
- `saida/` -- gerado (nao versionado): `songs.db`, `<id>_master.wav`, `<id>_stem_*.wav`

## Fluxo

1. Letra em portugues -> adaptacao para ingles -> folha de pronuncia (com o Claude).
2. Gerar: `uv run python scripts/caelum_gerar.py 01_semente` (use `--seed N` para outra tentativa).
3. No REAPER (projeto novo e vazio), com o MCP conectado: `reaper_build_vocal_session` com a pasta `caelum/01_semente/saida` e o id da musica. Cria as faixas dos stems, `guia_ia` (vocal da IA, silenciado, so para referencia) e `voz_caelum` (armada).
4. Escolha a entrada de audio da faixa `voz_caelum` no REAPER (depende da sua interface) e grave.
5. Mix e master (frente 4 da spec).

O vocal da IA (`guia_ia`) serve so de referencia de pronuncia/fraseado.
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore caelum/README.md caelum/_modelo
git commit -m "$(cat <<'EOF'
feat: estrutura caelum/ com modelos de faixa e regras de gitignore

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `caelum/faixa.py` -- ler a configuracao de uma faixa

**Files:**
- Create: `caelum/__init__.py` (vazio)
- Create: `caelum/faixa.py`
- Test: `tests/test_caelum_faixa.py`

**Interfaces:**
- Consumes: formato de `faixa.toml` / `letra_en.md` da Task 1.
- Produces:
  - `CAELUM_ROOT: Path` (a pasta `caelum/`)
  - `class FaixaError(ValueError)`
  - `@dataclass(frozen=True) class Faixa: dir: Path; prompt: str; lyrics: str; duration: float; seed: int; bpm: int | None; keyscale: str | None; vocal_language: str; lufs_target: float`
  - `load_faixa(faixa_dir: Path | str) -> Faixa`

- [ ] **Step 1: Write the failing tests**

`tests/test_caelum_faixa.py`:
```python
import pytest

from caelum.faixa import CAELUM_ROOT, Faixa, FaixaError, load_faixa


def _make_faixa(tmp_path, toml="prompt = \"nu metal\"\n", lyrics="[en]\n[Verse]\nhello\n"):
    (tmp_path / "faixa.toml").write_text(toml, encoding="utf-8")
    if lyrics is not None:
        (tmp_path / "letra_en.md").write_text(lyrics, encoding="utf-8")
    return tmp_path


def test_load_faixa_applies_defaults(tmp_path):
    faixa = load_faixa(_make_faixa(tmp_path))
    assert isinstance(faixa, Faixa)
    assert faixa.dir == tmp_path
    assert faixa.prompt == "nu metal"
    assert faixa.lyrics == "[en]\n[Verse]\nhello"
    assert faixa.duration == 180.0
    assert faixa.seed == 42
    assert faixa.bpm is None
    assert faixa.keyscale is None
    assert faixa.vocal_language == "en"
    assert faixa.lufs_target == -9.0


def test_load_faixa_reads_all_fields(tmp_path):
    toml = (
        'prompt = "nu metal"\nduration = 200\nseed = 7\nbpm = 140\n'
        'keyscale = "D minor"\nvocal_language = "en"\nlufs_target = -8.5\n'
    )
    faixa = load_faixa(_make_faixa(tmp_path, toml=toml))
    assert (faixa.duration, faixa.seed, faixa.bpm) == (200.0, 7, 140)
    assert faixa.keyscale == "D minor"
    assert faixa.lufs_target == -8.5


def test_load_faixa_rejects_unknown_key(tmp_path):
    with pytest.raises(FaixaError, match="bpn"):
        load_faixa(_make_faixa(tmp_path, toml='prompt = "x"\nbpn = 140\n'))


@pytest.mark.parametrize("toml", ["", 'prompt = ""\n', 'prompt = "   "\n', "prompt = 3\n"])
def test_load_faixa_rejects_missing_or_blank_prompt(tmp_path, toml):
    with pytest.raises(FaixaError, match="prompt"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("lyrics", ["", "  \n\n"])
def test_load_faixa_rejects_blank_lyrics(tmp_path, lyrics):
    with pytest.raises(FaixaError, match="letra_en.md"):
        load_faixa(_make_faixa(tmp_path, lyrics=lyrics))


def test_load_faixa_rejects_missing_files(tmp_path):
    with pytest.raises(FaixaError, match="faixa.toml"):
        load_faixa(tmp_path)
    (tmp_path / "faixa.toml").write_text('prompt = "x"\n', encoding="utf-8")
    with pytest.raises(FaixaError, match="letra_en.md"):
        load_faixa(tmp_path)


def test_load_faixa_rejects_invalid_toml_and_bad_values(tmp_path):
    with pytest.raises(FaixaError, match="invalido"):
        load_faixa(_make_faixa(tmp_path, toml="prompt = = x"))
    with pytest.raises(FaixaError, match="invalido"):
        load_faixa(_make_faixa(tmp_path, toml='prompt = "x"\nbpm = "rapido"\n'))


def test_modelo_is_a_loadable_faixa():
    faixa = load_faixa(CAELUM_ROOT / "_modelo")
    assert faixa.vocal_language == "en"
    assert faixa.lyrics.startswith("[en]")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_caelum_faixa.py -q`
Expected: FAIL/ERROR com `ModuleNotFoundError: No module named 'caelum'`.

- [ ] **Step 3: Write the implementation**

`caelum/__init__.py`: arquivo vazio.

`caelum/faixa.py`:
```python
"""Leitura da configuracao de uma faixa do album (faixa.toml + letra_en.md).

Ver docs/superpowers/specs/2026-10-02-caelum-album-design.md.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

CAELUM_ROOT = Path(__file__).resolve().parent

_ALLOWED_KEYS = {"prompt", "duration", "seed", "bpm", "keyscale", "vocal_language", "lufs_target"}


class FaixaError(ValueError):
    """Configuracao de faixa invalida ou incompleta."""


@dataclass(frozen=True)
class Faixa:
    dir: Path
    prompt: str
    lyrics: str
    duration: float
    seed: int
    bpm: int | None
    keyscale: str | None
    vocal_language: str
    lufs_target: float


def load_faixa(faixa_dir: Path | str) -> Faixa:
    """Le `faixa.toml` e `letra_en.md` de uma pasta de faixa.

    Falha cedo (FaixaError) em qualquer problema, para nao gastar uma geracao
    do Kaggle com configuracao quebrada: arquivos ausentes, TOML invalido,
    chave desconhecida, prompt vazio, letra vazia, valor de tipo errado.
    """
    faixa_dir = Path(faixa_dir)
    toml_path = faixa_dir / "faixa.toml"
    lyrics_path = faixa_dir / "letra_en.md"
    if not toml_path.is_file():
        raise FaixaError(f"faixa.toml nao encontrado em {faixa_dir}")
    if not lyrics_path.is_file():
        raise FaixaError(f"letra_en.md nao encontrado em {faixa_dir}")

    try:
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FaixaError(f"faixa.toml invalido: {exc}") from exc

    unknown = set(data) - _ALLOWED_KEYS
    if unknown:
        raise FaixaError(f"chave(s) desconhecida(s) em faixa.toml: {sorted(unknown)}")

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise FaixaError("faixa.toml precisa de 'prompt' (texto nao vazio)")

    lyrics = lyrics_path.read_text(encoding="utf-8").strip()
    if not lyrics:
        raise FaixaError(f"{lyrics_path.name} esta vazio")

    try:
        return Faixa(
            dir=faixa_dir,
            prompt=prompt.strip(),
            lyrics=lyrics,
            duration=float(data.get("duration", 180.0)),
            seed=int(data.get("seed", 42)),
            bpm=int(data["bpm"]) if "bpm" in data else None,
            keyscale=data.get("keyscale"),
            vocal_language=data.get("vocal_language", "en"),
            lufs_target=float(data.get("lufs_target", -9.0)),
        )
    except (TypeError, ValueError) as exc:
        raise FaixaError(f"valor invalido em faixa.toml: {exc}") from exc
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_caelum_faixa.py -q`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add caelum/__init__.py caelum/faixa.py tests/test_caelum_faixa.py
git commit -m "$(cat <<'EOF'
feat: caelum.faixa le e valida faixa.toml + letra_en.md

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `caelum/gerar.py` + `scripts/caelum_gerar.py` -- gerar uma faixa

**Files:**
- Create: `caelum/gerar.py`
- Create: `scripts/caelum_gerar.py`
- Test: `tests/test_caelum_gerar.py`

**Interfaces:**
- Consumes: `caelum.faixa.load_faixa/FaixaError/CAELUM_ROOT` (Task 2); `ace_step.song_db.create_song(db_path, prompt, duration, seed, bpm, keyscale, vocal_language) -> int`, `ace_step.song_db.get_song(db_path, song_id) -> dict | None`; `ace_step.orchestrator.run_generation(...)` (Task 0, assinatura do kernel batch).
- Produces:
  - `resolve_faixa_dir(arg: str, root: Path = CAELUM_ROOT) -> Path`
  - `gerar(faixa_dir: Path | str, *, seed: int | None = None, timeout: float = 2700.0) -> tuple[int, str, str | None]` retornando `(song_id, status, detail)`; saidas em `<faixa_dir>/saida/` (`songs.db`, `<id>_master.wav`, `<id>_stem_*.wav`).

- [ ] **Step 1: Write the failing tests**

`tests/test_caelum_gerar.py`:
```python
from unittest.mock import patch

import pytest

from ace_step import song_db
from caelum.faixa import FaixaError
from caelum.gerar import gerar, resolve_faixa_dir


def _make_faixa(root, name="01_teste", seed=42):
    faixa_dir = root / name
    faixa_dir.mkdir()
    (faixa_dir / "faixa.toml").write_text(
        f'prompt = "nu metal"\nduration = 90\nseed = {seed}\nbpm = 130\n', encoding="utf-8"
    )
    (faixa_dir / "letra_en.md").write_text("[en]\n[Verse]\nhello\n", encoding="utf-8")
    return faixa_dir


def test_resolve_faixa_dir_finds_slug_under_root(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    assert resolve_faixa_dir("01_teste", root=tmp_path) == faixa_dir


def test_resolve_faixa_dir_accepts_literal_path(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    assert resolve_faixa_dir(str(faixa_dir), root=tmp_path / "outro") == faixa_dir


def test_resolve_faixa_dir_raises_when_missing(tmp_path):
    with pytest.raises(FaixaError, match="99_nada"):
        resolve_faixa_dir("99_nada", root=tmp_path)


def test_gerar_runs_pipeline_with_faixa_config_and_saves_in_saida(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        song_id, status, detail = gerar(faixa_dir, timeout=99.0)

    assert (song_id, status, detail) == (1, "done", "x.wav")
    args, kwargs = mock_run.call_args
    assert args == (faixa_dir / "saida" / "songs.db", faixa_dir / "saida", 1)
    assert kwargs["prompt"] == "nu metal"
    assert kwargs["lyrics"] == "[en]\n[Verse]\nhello"
    assert kwargs["duration"] == 90.0
    assert kwargs["seed"] == 42
    assert kwargs["bpm"] == 130
    assert kwargs["vocal_language"] == "en"
    assert kwargs["lufs_target"] == -9.0
    assert kwargs["timeout"] == 99.0
    row = song_db.get_song(faixa_dir / "saida" / "songs.db", 1)
    assert row["seed"] == 42 and row["bpm"] == 130


def test_gerar_seed_override_is_used_and_recorded(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        gerar(faixa_dir, seed=7)
    assert mock_run.call_args.kwargs["seed"] == 7
    assert song_db.get_song(faixa_dir / "saida" / "songs.db", 1)["seed"] == 7


def test_gerar_second_run_creates_new_song_id_in_same_db(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch("caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")):
        first_id, _, _ = gerar(faixa_dir)
        second_id, _, _ = gerar(faixa_dir, seed=8)
    assert (first_id, second_id) == (1, 2)


def test_gerar_returns_error_status_without_raising(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("error", "kernel falhou")
    ):
        assert gerar(faixa_dir) == (1, "error", "kernel falhou")


def test_gerar_invalid_faixa_fails_before_touching_db_or_kaggle(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    (faixa_dir / "letra_en.md").write_text("   \n", encoding="utf-8")
    with patch("caelum.gerar.orchestrator.run_generation") as mock_run:
        with pytest.raises(FaixaError):
            gerar(faixa_dir)
    mock_run.assert_not_called()
    assert not (faixa_dir / "saida").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_caelum_gerar.py -q`
Expected: FAIL/ERROR `ModuleNotFoundError: No module named 'caelum.gerar'`.

- [ ] **Step 3: Write `caelum/gerar.py`**

```python
"""Gera uma faixa do album: le a config da pasta, chama o pipeline do ace_step
(kernel batch: ACE-Step + Demucs) e grava tudo em <faixa>/saida/.

Nao reescreve a geracao; so a configura. Ver
docs/superpowers/specs/2026-10-02-caelum-album-design.md.
"""

from pathlib import Path

from ace_step import orchestrator, song_db

from .faixa import CAELUM_ROOT, FaixaError, load_faixa


def resolve_faixa_dir(arg: str, root: Path = CAELUM_ROOT) -> Path:
    """Aceita o slug de uma faixa (ex.: '01_semente', procurado em `root`)
    ou um caminho literal para a pasta da faixa."""
    named = Path(root) / arg
    if named.is_dir():
        return named
    literal = Path(arg)
    if literal.is_dir():
        return literal
    raise FaixaError(f"pasta da faixa '{arg}' nao encontrada (procurei em {root} e como caminho)")


def gerar(
    faixa_dir: Path | str, *, seed: int | None = None, timeout: float = 2700.0
) -> tuple[int, str, str | None]:
    """Roda a geracao+separacao de uma faixa. Devolve (song_id, status, detalhe).

    Valida a faixa ANTES de criar a musica no banco ou falar com o Kaggle
    (FaixaError sobe). Depois, o pipeline nunca levanta: erros voltam como
    status "error" e ficam gravados na linha da musica.
    """
    faixa = load_faixa(faixa_dir)
    used_seed = faixa.seed if seed is None else seed
    saida = faixa.dir / "saida"
    db_path = saida / "songs.db"

    song_id = song_db.create_song(
        db_path,
        prompt=faixa.prompt,
        duration=faixa.duration,
        seed=used_seed,
        bpm=faixa.bpm,
        keyscale=faixa.keyscale,
        vocal_language=faixa.vocal_language,
    )
    status, detail = orchestrator.run_generation(
        db_path,
        saida,
        song_id,
        prompt=faixa.prompt,
        duration=faixa.duration,
        seed=used_seed,
        bpm=faixa.bpm,
        keyscale=faixa.keyscale,
        vocal_language=faixa.vocal_language,
        lufs_target=faixa.lufs_target,
        lyrics=faixa.lyrics,
        timeout=timeout,
    )
    return song_id, status, detail
```

- [ ] **Step 4: Write `scripts/caelum_gerar.py`**

```python
import os
import subprocess
import sys

if not sys.flags.utf8_mode:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    result = subprocess.run([sys.executable, __file__, *sys.argv[1:]], env=env)
    sys.exit(result.returncode)

import argparse
from pathlib import Path

# Rodando como `python scripts/caelum_gerar.py`, o Python so poe scripts/ no
# caminho de imports; a raiz do repo (onde moram ace_step/ e caelum/) fica de fora.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from caelum.faixa import FaixaError
from caelum.gerar import gerar, resolve_faixa_dir


def main():
    parser = argparse.ArgumentParser(
        description="Gera uma faixa do album Caelum (ACE-Step + Demucs no Kaggle) em <faixa>/saida/."
    )
    parser.add_argument("faixa", help="Slug da faixa (ex.: 01_semente) ou caminho da pasta")
    parser.add_argument("--seed", type=int, default=None, help="Sobrescreve a seed do faixa.toml")
    parser.add_argument("--timeout", type=float, default=2700.0)
    args = parser.parse_args()

    load_dotenv()

    try:
        faixa_dir = resolve_faixa_dir(args.faixa)
        song_id, status, detail = gerar(faixa_dir, seed=args.seed, timeout=args.timeout)
    except FaixaError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)

    if status == "error":
        print(f"Erro (musica #{song_id}): {detail}", file=sys.stderr)
        sys.exit(1)
    print(f"Musica #{song_id} pronta: {detail}")
    print(f"Stems em: {faixa_dir / 'saida'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_caelum_gerar.py -q`
Expected: todos PASS.

- [ ] **Step 6: Verificar o script de fora da raiz (Review Focus 5)**

Run (de outra pasta, so valida o caminho/erro, nao gera nada):
```bash
cd /c/estudos && uv run --project /c/estudos/daw_music_studio python /c/estudos/daw_music_studio/scripts/caelum_gerar.py 99_nada; echo "exit=$?"
```
Expected: `Erro: pasta da faixa '99_nada' nao encontrada ...` e `exit=1` (sem `ModuleNotFoundError`). Se aparecer `ModuleNotFoundError`, o `sys.path.insert` esta errado -- corrija.

- [ ] **Step 7: Commit**

```bash
git add caelum/gerar.py scripts/caelum_gerar.py tests/test_caelum_gerar.py
git commit -m "$(cat <<'EOF'
feat: caelum_gerar gera uma faixa do album na pasta da propria faixa

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `reaper_bridge/vocal_session.py` -- montar a sessao de gravacao

**Files:**
- Create: `reaper_bridge/vocal_session.py`
- Test: `tests/test_vocal_session.py`

**Interfaces:**
- Consumes: `reaper_bridge.project.import_audio(project, file_path, track_name=None)` (cria faixa nova e importa o audio; devolve a faixa), `reaper_bridge.project.create_track(project, name)`, `reaper_bridge.project.list_tracks(project) -> list[str]`, `reaper_bridge.errors.ReaperBridgeError`; faixa do reapy: `track.is_muted = bool`, `track.set_info_value("I_RECARM", 1)` (par de `get_info_value("I_RECARM")` ja usado em `reaper_bridge/audit.py:find_armed_tracks`).
- Produces: `build_vocal_session(project, stems_dir: str, song_id: int) -> list[str]` -- devolve os nomes das faixas criadas, na ordem `[stems..., "guia_ia" (se houver vocal), "voz_caelum"]`. Constantes de modulo: `STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")`, `GUIDE_TRACK_NAME = "guia_ia"`, `VOICE_TRACK_NAME = "voz_caelum"`.

Convencao de arquivos (a do orquestrador): `<stems_dir>/<song_id>_stem_<nome>.wav`. Nomes das faixas dos stems: `drums`, `bass`, `guitar`, `piano`, `other`; o stem `vocals` vira `guia_ia` (silenciado).

- [ ] **Step 1: Write the failing tests**

`tests/test_vocal_session.py`:
```python
from unittest.mock import patch

import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.vocal_session import build_vocal_session
from tests.fakes import FakeProject, FakeTrack


def _write_stems(tmp_path, song_id=3, names=("vocals", "drums", "bass", "guitar", "piano", "other")):
    for name in names:
        (tmp_path / f"{song_id}_stem_{name}.wav").write_bytes(b"RIFF")
    return str(tmp_path)


def _fake_import(project, file_path, track_name=None):
    return project.add_track(index=project.n_tracks, name=track_name)


def _build(project, stems_dir, song_id=3):
    with patch("reaper_bridge.vocal_session.import_audio", side_effect=_fake_import) as mock_import:
        created = build_vocal_session(project, stems_dir, song_id)
    return created, mock_import


def test_build_creates_stem_tracks_guide_and_armed_voice_track(tmp_path):
    project = FakeProject()
    created, mock_import = _build(project, _write_stems(tmp_path))

    assert created == ["drums", "bass", "guitar", "piano", "other", "guia_ia", "voz_caelum"]
    assert [t.name for t in project.tracks] == created
    guide = next(t for t in project.tracks if t.name == "guia_ia")
    assert guide.is_muted is True
    voice = next(t for t in project.tracks if t.name == "voz_caelum")
    assert voice.get_info_value("I_RECARM") == 1
    assert voice.is_muted is False
    imported_paths = [c.args[1] for c in mock_import.call_args_list]
    assert imported_paths[-1].endswith("3_stem_vocals.wav")


def test_stem_tracks_are_not_muted(tmp_path):
    project = FakeProject()
    _build(project, _write_stems(tmp_path))
    for name in ("drums", "bass", "guitar", "piano", "other"):
        assert next(t for t in project.tracks if t.name == name).is_muted is False


def test_build_without_vocals_stem_skips_guide_track(tmp_path):
    project = FakeProject()
    stems_dir = _write_stems(tmp_path, names=("drums", "bass", "guitar", "piano", "other"))
    created, _ = _build(project, stems_dir)
    assert "guia_ia" not in created
    assert created[-1] == "voz_caelum"


def test_build_raises_when_no_stem_files_found(tmp_path):
    project = FakeProject()
    with pytest.raises(ReaperBridgeError, match="nenhum stem"):
        _build(project, str(tmp_path))
    assert project.tracks == []


def test_build_ignores_stems_of_other_song_ids(tmp_path):
    project = FakeProject()
    stems_dir = _write_stems(tmp_path, song_id=1)
    with pytest.raises(ReaperBridgeError, match="nenhum stem"):
        _build(project, stems_dir, song_id=2)


@pytest.mark.parametrize("existing", ["voz_caelum", "guia_ia", "drums"])
def test_build_refuses_when_target_track_name_already_exists(tmp_path, existing):
    project = FakeProject([FakeTrack(existing)])
    with patch("reaper_bridge.vocal_session.import_audio", side_effect=_fake_import) as mock_import:
        with pytest.raises(ReaperBridgeError, match=existing):
            build_vocal_session(project, _write_stems(tmp_path), 3)
    mock_import.assert_not_called()
    assert [t.name for t in project.tracks] == [existing]


def test_build_twice_does_not_duplicate_tracks(tmp_path):
    project = FakeProject()
    stems_dir = _write_stems(tmp_path)
    _build(project, stems_dir)
    count_after_first = project.n_tracks
    with pytest.raises(ReaperBridgeError):
        _build(project, stems_dir)
    assert project.n_tracks == count_after_first


def test_build_raises_when_stems_dir_missing(tmp_path):
    with pytest.raises(ReaperBridgeError, match="pasta de stems"):
        _build(FakeProject(), str(tmp_path / "nao_existe"))


def test_build_wraps_arm_failure(tmp_path):
    class UnarmableProject(FakeProject):
        def add_track(self, index, name):
            track = super().add_track(index, name)
            if name == "voz_caelum":
                def boom(param, value):
                    raise RuntimeError("REAPER desconectado")
                track.set_info_value = boom
            return track

    project = UnarmableProject()
    with pytest.raises(ReaperBridgeError, match="armar"):
        _build(project, _write_stems(tmp_path))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_vocal_session.py -q`
Expected: FAIL/ERROR `ModuleNotFoundError: No module named 'reaper_bridge.vocal_session'`.

- [ ] **Step 3: Write the implementation**

`reaper_bridge/vocal_session.py`:
```python
from __future__ import annotations

import os

from .errors import ReaperBridgeError
from .project import create_track, import_audio, list_tracks

STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")
GUIDE_TRACK_NAME = "guia_ia"
VOICE_TRACK_NAME = "voz_caelum"


def _track_name_for(stem_name: str) -> str:
    return GUIDE_TRACK_NAME if stem_name == "vocals" else stem_name


def build_vocal_session(project, stems_dir: str, song_id: int) -> list[str]:
    """Monta a sessao de gravacao de uma faixa do album.

    Importa os stems `<song_id>_stem_<nome>.wav` de `stems_dir` como faixas
    (o stem `vocals` vira `guia_ia`, silenciado: so referencia de pronuncia e
    fraseado) e cria a faixa `voz_caelum`, armada para gravar. Se nao houver o
    stem `vocals` (base instrumental), nao cria `guia_ia`. Devolve os nomes das
    faixas criadas, na ordem de criacao.

    Falha ANTES de qualquer mudanca no projeto se a pasta nao existe, nao ha
    nenhum stem dessa musica, ou se alguma faixa-alvo ja existe no projeto
    (rodar duas vezes nao duplica nada nem toca em faixas do usuario).
    Escolher a entrada de audio da faixa `voz_caelum` e manual no REAPER.
    """
    if not os.path.isdir(stems_dir):
        raise ReaperBridgeError(f"pasta de stems não encontrada: {stems_dir}")

    stems = []
    for stem_name in STEM_NAMES:
        path = os.path.join(stems_dir, f"{song_id}_stem_{stem_name}.wav")
        if os.path.isfile(path):
            stems.append((stem_name, path))
    if not stems:
        raise ReaperBridgeError(
            f"nenhum stem da música {song_id} encontrado em {stems_dir} "
            f"(esperado: {song_id}_stem_<nome>.wav)"
        )

    # Guia fica por ultimo entre os stems: so a ordem de criacao das faixas muda.
    stems.sort(key=lambda item: item[0] == "vocals")
    target_names = [_track_name_for(name) for name, _ in stems] + [VOICE_TRACK_NAME]
    existing = set(list_tracks(project))
    clashes = [name for name in target_names if name in existing]
    if clashes:
        raise ReaperBridgeError(
            f"já existe(m) no projeto faixa(s) com o nome: {', '.join(clashes)} "
            "-- use um projeto novo e vazio para montar a sessão"
        )

    created = []
    for stem_name, path in stems:
        track_name = _track_name_for(stem_name)
        track = import_audio(project, path, track_name=track_name)
        if stem_name == "vocals":
            try:
                track.is_muted = True
            except Exception as exc:
                raise ReaperBridgeError(
                    "não foi possível silenciar a faixa guia_ia: verifique se o REAPER está aberto"
                ) from exc
        created.append(track_name)

    voice = create_track(project, VOICE_TRACK_NAME)
    try:
        voice.set_info_value("I_RECARM", 1)
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível armar a faixa voz_caelum para gravação: "
            "verifique se o REAPER está aberto"
        ) from exc
    created.append(VOICE_TRACK_NAME)
    return created
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_vocal_session.py -q`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add reaper_bridge/vocal_session.py tests/test_vocal_session.py
git commit -m "$(cat <<'EOF'
feat: build_vocal_session monta stems, guia_ia silenciado e voz_caelum armada

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Ferramenta MCP `reaper_build_vocal_session`

**Files:**
- Modify: `mcp_server.py` (import de `vocal_session` + nova tool, logo depois de `reaper_split_stems`)
- Modify: `tests/test_mcp_server.py` (import + 2 testes)

**Interfaces:**
- Consumes: `reaper_bridge.vocal_session.build_vocal_session(project, stems_dir, song_id) -> list[str]` (Task 4); `mcp_server._run(operation)` e `get_project()` (ja existentes).
- Produces: tool MCP `reaper_build_vocal_session(stems_dir: str, song_id: int) -> str`.

- [ ] **Step 1: Write the failing tests**

Em `tests/test_mcp_server.py`, acrescente `reaper_build_vocal_session` ao bloco `from mcp_server import (...)` (ordem alfabetica, depois de `reaper_audit_session`) e adicione ao final do arquivo:

```python
def test_reaper_build_vocal_session_lists_created_tracks():
    with patch("mcp_server.get_project", return_value=object()):
        with patch(
            "mcp_server.vocal_session.build_vocal_session",
            return_value=["drums", "guia_ia", "voz_caelum"],
        ) as mock_build:
            result = reaper_build_vocal_session("C:/stems", 3)
    mock_build.assert_called_once()
    assert mock_build.call_args.args[1:] == ("C:/stems", 3)
    assert "drums, guia_ia, voz_caelum" in result
    assert "voz_caelum" in result


def test_reaper_build_vocal_session_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", return_value=object()):
        with patch(
            "mcp_server.vocal_session.build_vocal_session",
            side_effect=ReaperBridgeError("já existe(m) no projeto faixa(s) com o nome: voz_caelum"),
        ):
            result = reaper_build_vocal_session("C:/stems", 3)
    assert result.startswith("Erro: já existe")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mcp_server.py -q`
Expected: ERROR de import (`cannot import name 'reaper_build_vocal_session'`).

- [ ] **Step 3: Implement**

Em `mcp_server.py`: troque o import por
```python
from reaper_bridge import audit, mastering, midi, mixing, stems, vocal_session
```
e, logo depois da funcao `reaper_split_stems`, adicione:
```python
@mcp.tool()
def reaper_build_vocal_session(stems_dir: str, song_id: int) -> str:
    """Monta a sessão de gravação de uma faixa do álbum: importa os stems
    (<song_id>_stem_<nome>.wav de stems_dir) como faixas, silencia o vocal da IA
    (faixa guia_ia, só referência) e cria a faixa voz_caelum armada para gravar.
    Use num projeto REAPER novo e vazio; falha se alguma dessas faixas já existir."""
    def operation():
        created = vocal_session.build_vocal_session(get_project(), stems_dir, song_id)
        return (
            f"Sessão montada: {', '.join(created)}. "
            "Escolha a entrada de áudio da faixa 'voz_caelum' no REAPER antes de gravar."
        )
    return _run(operation)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_mcp_server.py -q`
Expected: todos PASS.

- [ ] **Step 5: Rodar a suite completa**

Run: `uv run pytest -q`
Expected: tudo verde.

- [ ] **Step 6: Commit**

```bash
git add mcp_server.py tests/test_mcp_server.py
git commit -m "$(cat <<'EOF'
feat: tool MCP reaper_build_vocal_session

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Verificacao ao vivo do montador de sessao (REAPER)

**Files:** nenhum arquivo do repo muda (script temporario no scratchpad da sessao).

**Interfaces:**
- Consumes: `reaper_bridge.vocal_session.build_vocal_session` (Task 4), `reaper_bridge.connection.get_project`.
- Produces: confirmacao (ou nao) de que `track.set_info_value("I_RECARM", 1)` realmente arma a faixa e que `is_muted` silencia a faixa no REAPER real. Se falhar, a correcao entra neste task, com teste de regressao.

Pre-condicoes -- peca ao usuario: **abrir um projeto novo e vazio no REAPER** (File > New project; sem faixas) e confirmar. Nunca rodar em projeto com faixas reais (a funcao recusa se houver faixa com os mesmos nomes, mas o teste deve ser isolado mesmo assim).

- [ ] **Step 1: Gerar WAVs sinteticos curtos e rodar o montador**

Crie um script temporario no scratchpad da sessao (nao no repo) e rode com `uv run python <script>`:

```python
import tempfile, numpy as np, soundfile as sf
from pathlib import Path
from reaper_bridge.connection import get_project
from reaper_bridge.project import list_tracks
from reaper_bridge.vocal_session import build_vocal_session

project = get_project()
assert list_tracks(project) == [], f"projeto nao esta vazio: {list_tracks(project)}"

tmp = Path(tempfile.mkdtemp())
for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
    sf.write(tmp / f"9_stem_{name}.wav", np.zeros(44100, dtype="float32"), 44100)

created = build_vocal_session(project, str(tmp), 9)
print("criadas:", created)
for track in project.tracks:
    print(track.name, "| muted =", track.is_muted, "| recarm =", track.get_info_value("I_RECARM"))
```

Expected: `criadas: ['drums','bass','guitar','piano','other','guia_ia','voz_caelum']`; `guia_ia` com `muted = True`; `voz_caelum` com `recarm = 1.0`; demais `muted = False`, `recarm = 0.0`. Peca ao usuario para **confirmar visualmente** no REAPER: `guia_ia` com o botao de mute aceso, `voz_caelum` com o botao de gravacao armada (vermelho), cada stem numa faixa propria com o item de audio.

- [ ] **Step 2: Verificar a recusa ao rodar de novo**

Rode o mesmo `build_vocal_session(project, str(tmp), 9)` outra vez na mesma sessao.
Expected: `ReaperBridgeError: já existe(m) no projeto faixa(s) com o nome: ...` e **nenhuma faixa nova** no REAPER (conferir `list_tracks`).

- [ ] **Step 3: Se `I_RECARM` nao armou (recarm continua 0.0)**

Nao assuma a API. Inspecione no REAPER real: `uv run python -c "import reapy; p=reapy.Project(); t=p.tracks[-1]; print([a for a in dir(t) if 'arm' in a.lower() or 'rec' in a.lower()])"` e teste a alternativa que aparecer (ex.: `t.set_info_value('I_RECARM', 1.0)`, ou `reapy.reascript_api.SetMediaTrackInfo_Value(t.id, 'I_RECARM', 1)`). Corrija `build_vocal_session` (e o teste `test_build_creates_stem_tracks_guide_and_armed_voice_track` / `FakeTrack` em `tests/fakes.py` se a chamada mudar), rode `uv run pytest -q` e repita o Step 1.

- [ ] **Step 4: Limpar SOMENTE o que o teste criou**

No REAPER, o projeto era novo e vazio: peca ao usuario para **fechar o projeto sem salvar** (File > Close project, "No"/"Don't save"). Nao rode nenhum comando de remocao em massa de faixas. Apague a pasta temporaria `tmp` do teste.

- [ ] **Step 5: Commit (so se houve correcao no Step 3)**

```bash
git add reaper_bridge/vocal_session.py tests/fakes.py tests/test_vocal_session.py
git commit -m "$(cat <<'EOF'
fix: arma a faixa voz_caelum com a API confirmada ao vivo no REAPER

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```
Se nao houve correcao, nao ha commit; apenas reporte o resultado.

---

### Task 7: Faixa-piloto (sessao interativa com o usuario)

**Files:**
- Create: `caelum/01_<slug>/{letra_pt.md,letra_en.md,pronuncia.md,faixa.toml}` (copiados de `caelum/_modelo/`)
- Create: `caelum/01_<slug>/NOTAS_PILOTO.md`

**Interfaces:**
- Consumes: `scripts/caelum_gerar.py` (Task 3), `reaper_build_vocal_session` (Tasks 4-5), pipeline merged (Task 0).
- Produces: a faixa 01 pronta + `NOTAS_PILOTO.md` com o resultado dos 4 criterios da spec. Este task NAO e automatizavel: cada passo envolve o usuario (escolha, audicao, gravacao). Use `superpowers:verification-before-completion` antes de declarar o piloto concluido.

- [ ] **Step 1: Escolher a cena e o slug com o usuario**

Pergunte (uma pergunta de cada vez) qual cena do arco de Caelum sera a faixa-piloto. Criterio da spec: tem de ter **refrao limpo melodico + uma parte gritada**. Defina `NN=01` e um `<slug>` curto em ASCII (ex.: `01_semente`). Copie `caelum/_modelo/` para `caelum/01_<slug>/`.

- [ ] **Step 2: Letra em portugues (com o usuario)**

Escreva `letra_pt.md` com o usuario: contexto da cena, versos, refrao (limpo), ponte (gritada). Primeira pessoa, Caelum, sem rap, sem narrador. Mostre o rascunho e itere ate o usuario aprovar.

- [ ] **Step 3: Adaptacao para ingles**

Escreva `letra_en.md` (so a letra, com tags `[en]`, `[Verse]`, `[Chorus]`, `[Bridge]`; sem comentarios, pois o arquivo e enviado inteiro). Regras: mesmo sentido/emocao da versao em portugues, ingles natural (sem "ingles de tradutor"), silabas e acentos que cabem em uma melodia de nu metal (linhas curtas, rimas simples). Explique ao usuario cada escolha onde o ingles se afasta do portugues. Aprovacao do usuario.

- [ ] **Step 4: Folha de pronuncia**

Escreva `pronuncia.md`: tabela linha a linha (ingles | pronuncia em portugues | observacoes), silaba tonica em **negrito**, palavras dificeis marcadas (th, `-ed` final, r, h, vogais curtas/longas); se alguma palavra for muito dificil e houver alternativa boa, proponha trocar na `letra_en.md`.

- [ ] **Step 5: Configurar `faixa.toml`**

Preencha `prompt` (estilo: nu metal melodico, guitarras afinadas baixo, refrao limpo, ponte gritada, sem rap), `bpm`, `keyscale` (opcional), `duration`. Valide sem gastar Kaggle: `uv run python -c "from caelum.faixa import load_faixa; print(load_faixa('caelum/01_<slug>'))"` -- Expected: imprime a `Faixa` sem `FaixaError`.

- [ ] **Step 6: Gerar (ate 3-4 tentativas)**

Com o OK do usuario (gasta cota e leva ate ~45 min):
```bash
uv run python scripts/caelum_gerar.py 01_<slug>
uv run python scripts/caelum_gerar.py 01_<slug> --seed 7
```
Expected: `Musica #N pronta: ...` e, em `caelum/01_<slug>/saida/`, `N_master.wav` e `N_stem_{vocals,drums,bass,guitar,piano,other}.wav`. Peca ao usuario para ouvir `N_master.wav` e julgar o **criterio 1** (e nu metal? groove pesado, refrao melodico, parte gritada?). Se nao, ajuste `prompt`/seed e gere de novo (maximo ~4 tentativas); se nao acertar, **PARE** e leve ao usuario a decisao de repensar o genero (spec).

- [ ] **Step 7: Avaliar a separacao (criterio 2)**

Peca ao usuario para ouvir os stems `drums`, `bass`, `guitar`, `other` **sem** o `vocals`. Ha vazamento de vocal que brigaria com a voz dele? Se sim: plano B da spec (gerar a base sem vocal/instrumental e usar um vocal guia a parte) -- registre e discuta com o usuario antes de seguir.

- [ ] **Step 8: Montar a sessao no REAPER e gravar (criterios 3 e 4)**

No REAPER, projeto novo e vazio: chame `reaper_build_vocal_session` com `stems_dir=<caminho absoluto de caelum/01_<slug>/saida>` e o `song_id` escolhido. O usuario escolhe a entrada de audio de `voz_caelum`, ouve o `guia_ia` (referencia) e grava a voz limpa e o grito com a `pronuncia.md` na mao. **Criterio 3:** consegue gravar a musica inteira em um numero razoavel de takes, sem travar sempre nas mesmas palavras? Anote as palavras problematicas.

- [ ] **Step 9: Mixagem rapida de teste**

Com o usuario: ajuste volumes/pan com as tools existentes (`reaper_set_volume`, `reaper_set_pan`, `reaper_add_fx`), `reaper_apply_master`, e `reaper_render` para um WAV de teste em `caelum/01_<slug>/saida/mix_teste.wav`. **Criterio 4:** stems em faixas, voz gravada na faixa dedicada, mixagem de teste com tudo junto.

- [ ] **Step 10: Registrar o resultado do piloto**

Escreva `caelum/01_<slug>/NOTAS_PILOTO.md`: para cada um dos 4 criterios, PASSOU/FALHOU/PARCIAL + observacoes do usuario (prompt/seed que funcionaram, palavras problematicas, ajustes de pronuncia, ideias para as outras 9 faixas, qual plano B foi usado se algum). Se um criterio falhou, diga o que a spec preve (plano B ou repensar o genero).

- [ ] **Step 11: Commit**

```bash
git add caelum/01_<slug>/letra_pt.md caelum/01_<slug>/letra_en.md caelum/01_<slug>/pronuncia.md caelum/01_<slug>/faixa.toml caelum/01_<slug>/NOTAS_PILOTO.md
git commit -m "$(cat <<'EOF'
feat: faixa-piloto 01 do album Caelum (letras, pronuncia, config e notas do piloto)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
)"
```

Depois do piloto, o proximo passo (fora deste plano) e a frente 2 (biblia do album), com spec propria.

---

## Self-review (feito ao escrever o plano)

**Cobertura da spec:**
- Passo zero (merge + teste ao vivo) -> Task 0. Fluxo de 7 etapas por faixa: etapas 1-3 (letra/idioma/pronuncia) -> Task 7 steps 2-4 + modelos (Task 1); etapas 4-5 (ACE-Step + Demucs, guia guardado) -> Task 0/3 e `guia_ia` (Task 4); etapa 6 (gravar) -> Task 7 step 8; etapa 7 (mix) -> Task 7 step 9.
- Componente 1 (estrutura `caelum/`, gitignore) -> Task 1. Componente 2 (etapa de idioma = processo) -> modelos + Task 7. Componente 3 (comando de geracao) -> Task 3. Componente 4 (montador + MCP + verificacao ao vivo em faixas temporarias) -> Tasks 4-6. Componente 5 (mix/master com ferramentas existentes) -> Task 7 step 9.
- Criterios de sucesso 1-4 e planos B -> Task 7 steps 6-10. Testes (automatizados + ao vivo + suite completa) -> Tasks 2-5, 6, 0/5.
- Lacuna conhecida e intencional: `music-main/` (a remocao e feita pelo usuario, como ele disse); nao ha task para isso.

**Placeholders:** `<slug>`/`NN` em Task 7 sao parametros escolhidos com o usuario no step 1 (nao placeholders de conteudo); nenhum "TBD/TODO".

**Consistencia de tipos:** `load_faixa -> Faixa` (Task 2) usado em `gerar` (Task 3) com os mesmos campos; `gerar -> (song_id, status, detail)` usado em `scripts/caelum_gerar.py`; `build_vocal_session(project, stems_dir, song_id) -> list[str]` identico em Tasks 4, 5 e 6; arquivos `<song_id>_stem_<nome>.wav` casam com o que `orchestrator.run_generation` grava (`output_dir / f"{song_id}_stem_{name}.wav"`, nomes `vocals, drums, bass, guitar, piano, other`).

**Review Focus:** (1) chave desconhecida -> `test_load_faixa_rejects_unknown_key`; (2) letra/prompt vazios -> testes de `load_faixa` + `test_gerar_invalid_faixa_fails_before_touching_db_or_kaggle`; (3) duplicacao -> `test_build_refuses_when_target_track_name_already_exists`, `test_build_twice_does_not_duplicate_tracks`, Task 6 step 2; (4) sem stems / sem vocals -> `test_build_raises_when_no_stem_files_found`, `test_build_without_vocals_stem_skips_guide_track`; (5) cwd diferente -> Task 3 step 6.
