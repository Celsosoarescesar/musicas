# REAPER Copilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao Claude Code, via um servidor MCP local, o poder de controlar o REAPER de verdade (criar/importar faixas, mixar, masterizar, gerar e analisar MIDI no piano roll) a partir de comandos em linguagem natural.

**Architecture:** `reapy` fala com o REAPER (aberto, ao vivo). Um pacote Python `reaper_bridge/` encapsula toda a lógica de negócio (projeto/faixas, mixagem, masterização, MIDI com `music21`) por trás de funções puras que recebem o projeto como parâmetro — o que as torna testáveis sem REAPER, via objetos falsos (`tests/fakes.py`). Um servidor MCP (`mcp_server.py`, SDK oficial `mcp`, classe `MCPServer`) expõe cada função como uma ferramenta, traduzindo qualquer `ReaperBridgeError` numa mensagem de erro em vez de deixar a exceção vazar.

**Tech Stack:** Python 3.11, `python-reapy` (já instalado), `mcp` (SDK oficial, `MCPServer`), `music21`, `pytest`, `uv`.

**Spec:** `docs/superpowers/specs/2026-09-26-reaper-copilot-design.md`

## Global Constraints

- Projeto independente em `C:\estudos\daw_music_studio`, Python `>=3.11`, dependências e `.venv` geridos pelo `uv` deste diretório — nunca o `.venv` de `music_studio/`.
- Toda função pública de `reaper_bridge` levanta `ReaperBridgeError` em qualquer falha esperada; nunca deixa uma exceção crua do `reapy`/SO vazar para quem chamou.
- Toda ferramenta MCP captura `ReaperBridgeError` e devolve uma string `"Erro: ..."`; nenhuma chamada pode derrubar o servidor com uma exceção não tratada.
- `render_project` só suporta saída `.wav` nesta versão.
- A chain de master usa só plugins nativos do REAPER (`ReaEQ (Cockos)`, `ReaComp (Cockos)`, `ReaLimit (Cockos)`) — nada de plugin de terceiro a instalar.
- `get_project()` precisa de timeout explícito: já vimos ao vivo, nesta mesma máquina, uma chamada ao `reapy` travar indefinidamente quando a configuração estava quebrada — não pode travar o servidor MCP.

## Review Focus

- REAPER fechado quando uma ferramenta é chamada → `get_project()` deve falhar rápido (timeout), não travar. (Task 1)
- Duas faixas com o mesmo nome no projeto → `find_track` deve recusar a ambiguidade em vez de agir silenciosamente na faixa errada. (Task 2)
- Importar um arquivo inexistente ou com extensão não suportada → falhar antes de chamar o REAPER, evitando travar como aconteceu com o script de inicialização quebrado durante a configuração. (Task 3)
- Renderizar para uma pasta que não existe, ou pedir um formato diferente de `.wav` → falhar com mensagem clara antes de acionar o REAPER. (Task 7)
- Pedir uma escala/tonalidade/grau inválido na geração musical → virar `ReaperBridgeError` com as opções válidas, não um traceback cru do `music21`. (Task 8)

---

## Task 1: Scaffolding, erros e conexão com timeout

**Files:**
- Modify: `pyproject.toml`
- Create: `reaper_bridge/__init__.py`
- Create: `reaper_bridge/errors.py`
- Create: `reaper_bridge/connection.py`
- Create: `tests/fakes.py`
- Test: `tests/test_connection.py`

**Interfaces:**
- Produces: `ReaperBridgeError(Exception)` (em `reaper_bridge.errors`); `get_project(timeout: float = 5.0) -> reapy.Project` (em `reaper_bridge.connection`); fakes `FakeProject`, `FakeTrack`, `FakeFX`, `FakeFXParam`, `FakeItem`, `FakeTake`, `FakeNote` (em `tests.fakes`), usados por todas as tasks seguintes.

- [ ] **Step 1: Adicionar dependências**

Rodar, a partir de `C:\estudos\daw_music_studio`:
```bash
uv add mcp music21
uv add --dev pytest
```

- [ ] **Step 2: Configurar o pytest**

Editar `pyproject.toml`, acrescentando ao final:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Criar o pacote `reaper_bridge`**

`reaper_bridge/__init__.py`:
```python
```
(arquivo vazio, só marca o diretório como pacote)

`reaper_bridge/errors.py`:
```python
class ReaperBridgeError(Exception):
    """Erro de negócio do reaper_bridge, com mensagem pronta para mostrar ao usuário."""
```

- [ ] **Step 4: Criar os fakes de teste**

`tests/fakes.py`:
```python
"""Fakes leves para simular objetos do reapy nos testes, sem precisar do REAPER aberto."""


class FakeNote:
    def __init__(self, pitch, start=0.0, end=1.0, velocity=100):
        self.pitch = pitch
        self.start = start
        self.end = end
        self.velocity = velocity


class FakeTake:
    def __init__(self, is_midi=True):
        self.is_midi = is_midi
        self.notes = []

    def add_note(self, start, end, pitch, velocity=100, channel=0, unit="seconds"):
        note = FakeNote(pitch, start=start, end=end, velocity=velocity)
        self.notes.append(note)
        return note


class FakeItem:
    def __init__(self, start=0.0, end=1.0):
        self.start = start
        self.end = end
        self.active_take = FakeTake()


class FakeFXParam:
    def __init__(self, name, normalized=0.0):
        self.name = name
        self.normalized = normalized


class FakeFX:
    def __init__(self, name, param_names=()):
        self.name = name
        self.params = [FakeFXParam(param_name) for param_name in param_names]


class FakeTrack:
    def __init__(self, name, volume=1.0, pan=0.0, is_muted=False, is_solo=False):
        self.name = name
        self.volume = volume
        self.pan = pan
        self.is_muted = is_muted
        self.is_solo = is_solo
        self.fxs = []
        self.items = []

    def add_fx(self, fx_name):
        fx = FakeFX(fx_name)
        self.fxs.append(fx)
        return fx

    def add_midi_item(self, start=0.0, end=1.0):
        item = FakeItem(start=start, end=end)
        self.items.append(item)
        return item


class FakeProject:
    def __init__(self, tracks=None):
        self.tracks = list(tracks or [])
        self.cursor_position = 0.0
        self.master_track = FakeTrack("MASTER")
        self._info_strings = {}

    @property
    def n_tracks(self):
        return len(self.tracks)

    def add_track(self, index, name):
        track = FakeTrack(name)
        self.tracks.insert(index, track)
        return track

    def set_info_string(self, param_name, value):
        self._info_strings[param_name] = value

    def get_info_string(self, param_name):
        return self._info_strings.get(param_name, "")
```

- [ ] **Step 5: Escrever os testes de conexão (falhando)**

`tests/test_connection.py`:
```python
import time
from unittest.mock import patch

import pytest

from reaper_bridge.connection import get_project
from reaper_bridge.errors import ReaperBridgeError


def test_get_project_returns_project_when_reaper_responds():
    fake_project = object()
    with patch("reaper_bridge.connection.reapy.Project", return_value=fake_project):
        assert get_project(timeout=1.0) is fake_project


def test_get_project_raises_bridge_error_on_timeout():
    def slow_call():
        time.sleep(2)

    with patch("reaper_bridge.connection.reapy.Project", side_effect=slow_call):
        with pytest.raises(ReaperBridgeError):
            get_project(timeout=0.1)


def test_get_project_raises_bridge_error_on_connection_exception():
    with patch("reaper_bridge.connection.reapy.Project", side_effect=RuntimeError("boom")):
        with pytest.raises(ReaperBridgeError):
            get_project(timeout=1.0)
```

- [ ] **Step 6: Rodar os testes e confirmar que falham**

Run: `uv run pytest tests/test_connection.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'reaper_bridge.connection'`

- [ ] **Step 7: Implementar `connection.py`**

```python
from __future__ import annotations

import concurrent.futures

import reapy

from .errors import ReaperBridgeError

CONNECTION_TIMEOUT_SECONDS = 5.0


def get_project(timeout: float = CONNECTION_TIMEOUT_SECONDS) -> "reapy.Project":
    """Retorna o projeto REAPER atualmente aberto, ou levanta ReaperBridgeError."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(reapy.Project)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            raise ReaperBridgeError(
                "REAPER não respondeu a tempo. Verifique se o REAPER está aberto e se o "
                "reapy foi configurado corretamente (veja o README)."
            ) from exc
        except Exception as exc:  # reapy pode levantar erros variados de conexão
            raise ReaperBridgeError(
                "REAPER não está aberto ou não foi configurado corretamente, abra o REAPER "
                "e tente de novo."
            ) from exc
```

- [ ] **Step 8: Rodar os testes e confirmar que passam**

Run: `uv run pytest tests/test_connection.py -v`
Expected: PASS (3 testes)

- [ ] **Step 9: Verificação manual contra o REAPER real**

Com o REAPER aberto:
```bash
uv run python -c "from reaper_bridge.connection import get_project; print(get_project())"
```
Esperado: imprime o projeto (`Project("...")`), sem erro. Feche o REAPER e rode de novo — esperado: `reaper_bridge.errors.ReaperBridgeError` numa mensagem clara (não um travamento).

- [ ] **Step 10: Commit**

```bash
git add pyproject.toml uv.lock reaper_bridge tests
git commit -m "feat: scaffolding, ReaperBridgeError e conexão com timeout"
```

---

## Task 2: Faixas — listar, criar, renomear

**Files:**
- Create: `reaper_bridge/project.py`
- Test: `tests/test_project.py`

**Interfaces:**
- Consumes: `FakeProject`, `FakeTrack` (de `tests.fakes`, Task 1); `ReaperBridgeError` (Task 1).
- Produces: `list_tracks(project) -> list[str]`; `find_track(project, name) -> Track` (usado por `mixing.py`, `mastering.py`, `midi.py` nas próximas tasks); `create_track(project, name) -> Track`; `rename_track(project, name, new_name) -> Track`.

- [ ] **Step 1: Escrever os testes (falhando)**

`tests/test_project.py`:
```python
import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.project import create_track, find_track, list_tracks, rename_track
from tests.fakes import FakeProject, FakeTrack


def test_list_tracks_returns_track_names():
    project = FakeProject([FakeTrack("bateria"), FakeTrack("baixo")])
    assert list_tracks(project) == ["bateria", "baixo"]


def test_find_track_returns_matching_track():
    drums = FakeTrack("bateria")
    project = FakeProject([drums, FakeTrack("baixo")])
    assert find_track(project, "bateria") is drums


def test_find_track_raises_with_available_names_when_missing():
    project = FakeProject([FakeTrack("bateria")])
    with pytest.raises(ReaperBridgeError, match="bateria"):
        find_track(project, "voz")


def test_find_track_raises_when_name_is_ambiguous():
    project = FakeProject([FakeTrack("voz"), FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="mais de uma"):
        find_track(project, "voz")


def test_create_track_appends_new_track():
    project = FakeProject([FakeTrack("bateria")])
    track = create_track(project, "baixo")
    assert track.name == "baixo"
    assert list_tracks(project) == ["bateria", "baixo"]


def test_rename_track_changes_name():
    project = FakeProject([FakeTrack("bateria")])
    rename_track(project, "bateria", "drums")
    assert list_tracks(project) == ["drums"]
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_project.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'reaper_bridge.project'`

- [ ] **Step 3: Implementar `project.py`**

```python
from __future__ import annotations

import reapy

from .errors import ReaperBridgeError


def list_tracks(project: "reapy.Project") -> list[str]:
    return [track.name for track in project.tracks]


def find_track(project: "reapy.Project", name: str):
    matches = [track for track in project.tracks if track.name == name]
    if not matches:
        available = ", ".join(list_tracks(project)) or "(nenhuma)"
        raise ReaperBridgeError(
            f"faixa '{name}' não existe, faixas disponíveis: {available}"
        )
    if len(matches) > 1:
        raise ReaperBridgeError(
            f"existe mais de uma faixa chamada '{name}' ({len(matches)} faixas), "
            "renomeie as faixas duplicadas antes de continuar"
        )
    return matches[0]


def create_track(project: "reapy.Project", name: str):
    return project.add_track(index=project.n_tracks, name=name)


def rename_track(project: "reapy.Project", name: str, new_name: str):
    track = find_track(project, name)
    track.name = new_name
    return track
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_project.py -v`
Expected: PASS (6 testes)

- [ ] **Step 5: Verificação manual contra o REAPER real**

Com o REAPER aberto, projeto vazio:
```bash
uv run python -c "
from reaper_bridge.connection import get_project
from reaper_bridge.project import create_track, list_tracks
p = get_project()
create_track(p, 'teste')
print(list_tracks(p))
"
```
Esperado: aparece uma faixa nova chamada "teste" na tela do REAPER, e o comando imprime `['teste']` (ou a faixa some da lista anterior + 'teste', se já havia faixas).

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/project.py tests/test_project.py
git commit -m "feat: listar, criar e renomear faixas no REAPER"
```

---

## Task 3: Importar áudio como nova faixa

**Files:**
- Modify: `reaper_bridge/project.py`
- Modify: `tests/test_project.py`

**Interfaces:**
- Consumes: `find_track`, `list_tracks` (Task 2); `reapy.reascript_api.RPR_InsertMedia(file: str, mode: int)` (API bruta do ReaScript, sem wrapper no `reapy`).
- Produces: `import_audio(project, file_path: str, track_name: str | None = None) -> Track`.

- [ ] **Step 1: Acrescentar os testes (falhando)**

Adicionar ao final de `tests/test_project.py`:
```python
from unittest.mock import patch

from reaper_bridge.project import import_audio


def test_import_audio_raises_when_file_missing():
    project = FakeProject([])
    with pytest.raises(ReaperBridgeError, match="não encontrado"):
        import_audio(project, "C:/nao/existe.wav")


def test_import_audio_raises_for_unsupported_extension(tmp_path):
    file_path = tmp_path / "musica.xyz"
    file_path.write_bytes(b"fake")
    project = FakeProject([])
    with pytest.raises(ReaperBridgeError, match="não suportada"):
        import_audio(project, str(file_path))


def test_import_audio_inserts_media_and_renames_new_track(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    def fake_insert_media(path, mode):
        project.tracks.append(FakeTrack("stem"))

    with patch(
        "reaper_bridge.project.reapy.reascript_api.RPR_InsertMedia",
        side_effect=fake_insert_media,
    ) as mock_insert:
        track = import_audio(project, str(file_path), track_name="voz")

    mock_insert.assert_called_once_with(str(file_path), 1)
    assert track.name == "voz"
    assert list_tracks(project) == ["bateria", "voz"]
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_project.py -v -k import_audio`
Expected: FAIL com `ImportError: cannot import name 'import_audio'`

- [ ] **Step 3: Implementar `import_audio`**

Acrescentar ao final de `reaper_bridge/project.py`:
```python
import os

_SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".aiff"}


def import_audio(
    project: "reapy.Project", file_path: str, track_name: str | None = None
):
    if not os.path.isfile(file_path):
        raise ReaperBridgeError(f"arquivo de áudio não encontrado: {file_path}")
    extension = os.path.splitext(file_path)[1].lower()
    if extension not in _SUPPORTED_AUDIO_EXTENSIONS:
        raise ReaperBridgeError(
            f"extensão '{extension}' não suportada, use um destes formatos: "
            f"{', '.join(sorted(_SUPPORTED_AUDIO_EXTENSIONS))}"
        )
    project.cursor_position = 0.0
    reapy.reascript_api.RPR_InsertMedia(file_path, 1)  # mode 1 = adicionar em nova faixa
    track = project.tracks[-1]
    if track_name:
        track.name = track_name
    return track
```

(mover o `import os` para o topo do arquivo, junto com o `import reapy` já existente, em vez de deixá-lo no meio do arquivo)

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_project.py -v`
Expected: PASS (9 testes)

- [ ] **Step 5: Verificação manual contra o REAPER real**

Com o REAPER aberto, use um `.wav` real (por exemplo, um stem já gerado em
`music_studio/projects/ace-step-orchestrator/output/`):
```bash
uv run python -c "
from reaper_bridge.connection import get_project
from reaper_bridge.project import import_audio
p = get_project()
import_audio(p, r'C:\estudos\daw_music_studio\music_studio\projects\ace-step-orchestrator\output\3_master.wav', track_name='teste_import')
"
```
Esperado: uma nova faixa "teste_import" aparece no REAPER com o áudio importado a partir do início (posição 0).

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/project.py tests/test_project.py
git commit -m "feat: importar arquivo de audio como nova faixa"
```

---

## Task 4: Mixagem — volume, pan, mute, solo

**Files:**
- Create: `reaper_bridge/mixing.py`
- Test: `tests/test_mixing.py`

**Interfaces:**
- Consumes: `find_track` (Task 2), `ReaperBridgeError` (Task 1).
- Produces: `set_volume(project, track_name, db) -> Track`; `set_pan(project, track_name, pan) -> Track`; `set_mute(project, track_name, muted: bool) -> Track`; `set_solo(project, track_name, solo: bool) -> Track`.

- [ ] **Step 1: Escrever os testes (falhando)**

`tests/test_mixing.py`:
```python
import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.mixing import set_mute, set_pan, set_solo, set_volume
from tests.fakes import FakeProject, FakeTrack


def test_set_volume_converts_db_to_linear_gain():
    project = FakeProject([FakeTrack("voz")])
    set_volume(project, "voz", 0.0)
    assert project.tracks[0].volume == pytest.approx(1.0)


def test_set_volume_raises_when_out_of_range():
    project = FakeProject([FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="dB"):
        set_volume(project, "voz", 50.0)


def test_set_pan_sets_value():
    project = FakeProject([FakeTrack("voz")])
    set_pan(project, "voz", -0.5)
    assert project.tracks[0].pan == -0.5


def test_set_pan_raises_when_out_of_range():
    project = FakeProject([FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="pan"):
        set_pan(project, "voz", 2.0)


def test_set_mute_toggles_flag():
    project = FakeProject([FakeTrack("voz")])
    set_mute(project, "voz", True)
    assert project.tracks[0].is_muted is True


def test_set_solo_toggles_flag():
    project = FakeProject([FakeTrack("voz")])
    set_solo(project, "voz", True)
    assert project.tracks[0].is_solo is True
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_mixing.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'reaper_bridge.mixing'`

- [ ] **Step 3: Implementar `mixing.py`**

```python
from __future__ import annotations

from .errors import ReaperBridgeError
from .project import find_track

MIN_DB = -150.0
MAX_DB = 12.0


def _db_to_linear(db: float) -> float:
    return 10 ** (db / 20)


def set_volume(project, track_name: str, db: float):
    if not MIN_DB <= db <= MAX_DB:
        raise ReaperBridgeError(
            f"volume deve estar entre {MIN_DB} e {MAX_DB} dB, recebido: {db}"
        )
    track = find_track(project, track_name)
    track.volume = _db_to_linear(db)
    return track


def set_pan(project, track_name: str, pan: float):
    if not -1.0 <= pan <= 1.0:
        raise ReaperBridgeError(f"pan deve estar entre -1.0 e 1.0, recebido: {pan}")
    track = find_track(project, track_name)
    track.pan = pan
    return track


def set_mute(project, track_name: str, muted: bool):
    track = find_track(project, track_name)
    track.is_muted = muted
    return track


def set_solo(project, track_name: str, solo: bool):
    track = find_track(project, track_name)
    track.is_solo = solo
    return track
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_mixing.py -v`
Expected: PASS (6 testes)

- [ ] **Step 5: Verificação manual contra o REAPER real**

Com o REAPER aberto e uma faixa chamada "teste_import" (da Task 3):
```bash
uv run python -c "
from reaper_bridge.connection import get_project
from reaper_bridge.mixing import set_volume, set_pan
p = get_project()
set_volume(p, 'teste_import', -6.0)
set_pan(p, 'teste_import', -0.3)
"
```
Esperado: o fader de volume da faixa se move para -6dB e o pan para a esquerda, visíveis na tela do REAPER.

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/mixing.py tests/test_mixing.py
git commit -m "feat: volume, pan, mute e solo por faixa"
```

---

## Task 5: Mixagem — plugins (FX) e parâmetros

**Files:**
- Modify: `reaper_bridge/mixing.py`
- Modify: `tests/test_mixing.py`

**Interfaces:**
- Consumes: `find_track` (Task 2); `Track.add_fx(name) -> FX` (levanta `ValueError` se o plugin não existir); `FX.params` (lista de `FXParam`, cada um com `.name` e `.normalized`).
- Produces: `add_fx(project, track_name, fx_name) -> FX`; `set_fx_param(project, track_name, fx_name, param_name, value: float) -> FXParam`.

- [ ] **Step 1: Acrescentar os testes (falhando)**

Adicionar ao final de `tests/test_mixing.py`:
```python
from reaper_bridge.mixing import add_fx, set_fx_param
from tests.fakes import FakeFX


def test_add_fx_adds_plugin_to_track():
    project = FakeProject([FakeTrack("voz")])
    fx = add_fx(project, "voz", "ReaEQ (Cockos)")
    assert fx.name == "ReaEQ (Cockos)"
    assert project.tracks[0].fxs[0] is fx


def test_add_fx_raises_when_plugin_unknown():
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]

    def raise_value_error(name):
        raise ValueError("fx not found")

    track.add_fx = raise_value_error
    with pytest.raises(ReaperBridgeError, match="não encontrado"):
        add_fx(project, "voz", "PluginQueNaoExiste")


def test_set_fx_param_updates_normalized_value():
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]
    track.fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold", "Ratio"]))
    set_fx_param(project, "voz", "ReaComp (Cockos)", "Threshold", 0.6)
    assert track.fxs[0].params[0].normalized == 0.6


def test_set_fx_param_raises_for_unknown_param():
    project = FakeProject([FakeTrack("voz")])
    project.tracks[0].fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold"]))
    with pytest.raises(ReaperBridgeError, match="não existe"):
        set_fx_param(project, "voz", "ReaComp (Cockos)", "ParametroInexistente", 0.5)


def test_set_fx_param_raises_when_value_out_of_range():
    project = FakeProject([FakeTrack("voz")])
    project.tracks[0].fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold"]))
    with pytest.raises(ReaperBridgeError, match="0.0 e 1.0"):
        set_fx_param(project, "voz", "ReaComp (Cockos)", "Threshold", 2.0)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_mixing.py -v -k "fx"`
Expected: FAIL com `ImportError: cannot import name 'add_fx'`

- [ ] **Step 3: Implementar `add_fx` e `set_fx_param`**

Acrescentar ao final de `reaper_bridge/mixing.py`:
```python
def _find_fx(track, fx_name: str):
    for fx in track.fxs:
        if fx.name == fx_name:
            return fx
    available = ", ".join(fx.name for fx in track.fxs) or "(nenhum)"
    raise ReaperBridgeError(
        f"plugin '{fx_name}' não está na faixa, plugins presentes: {available}"
    )


def add_fx(project, track_name: str, fx_name: str):
    track = find_track(project, track_name)
    try:
        return track.add_fx(fx_name)
    except ValueError as exc:
        raise ReaperBridgeError(f"plugin '{fx_name}' não encontrado no REAPER") from exc


def set_fx_param(project, track_name: str, fx_name: str, param_name: str, value: float):
    if not 0.0 <= value <= 1.0:
        raise ReaperBridgeError(
            f"valor de parâmetro deve estar entre 0.0 e 1.0 (normalizado), recebido: {value}"
        )
    track = find_track(project, track_name)
    fx = _find_fx(track, fx_name)
    param = next((p for p in fx.params if p.name == param_name), None)
    if param is None:
        available = ", ".join(p.name for p in fx.params) or "(nenhum)"
        raise ReaperBridgeError(
            f"parâmetro '{param_name}' não existe em '{fx_name}', parâmetros "
            f"disponíveis: {available}"
        )
    param.normalized = value
    return param
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_mixing.py -v`
Expected: PASS (11 testes)

- [ ] **Step 5: Verificação manual contra o REAPER real**

Com o REAPER aberto e a faixa "teste_import":
```bash
uv run python -c "
from reaper_bridge.connection import get_project
from reaper_bridge.mixing import add_fx
p = get_project()
fx = add_fx(p, 'teste_import', 'ReaEQ (Cockos)')
print(fx.name, [param.name for param in fx.params][:5])
"
```
Esperado: o ReaEQ aparece na chain de FX da faixa no REAPER, e o comando imprime o nome do plugin e os primeiros nomes de parâmetro reais (confirma que `fx.params[i].name` é o formato certo para usar em `set_fx_param`).

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/mixing.py tests/test_mixing.py
git commit -m "feat: adicionar plugins e ajustar parametros nas faixas"
```

---

## Task 6: Masterização — chain padrão na faixa mestre

**Files:**
- Create: `reaper_bridge/mastering.py`
- Test: `tests/test_mastering.py`

**Interfaces:**
- Consumes: `Project.master_track` (Track); `Track.add_fx(name) -> FX` (Task 5).
- Produces: `MASTER_CHAIN_PLUGINS: list[str]`; `apply_master_chain(project) -> list[FX]`.

- [ ] **Step 1: Escrever os testes (falhando)**

`tests/test_mastering.py`:
```python
from reaper_bridge.mastering import MASTER_CHAIN_PLUGINS, apply_master_chain
from tests.fakes import FakeProject


def test_apply_master_chain_adds_all_plugins_to_master_track():
    project = FakeProject([])
    fxs = apply_master_chain(project)
    assert [fx.name for fx in fxs] == MASTER_CHAIN_PLUGINS
    assert [fx.name for fx in project.master_track.fxs] == MASTER_CHAIN_PLUGINS
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_mastering.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'reaper_bridge.mastering'`

- [ ] **Step 3: Implementar `apply_master_chain`**

`reaper_bridge/mastering.py`:
```python
from __future__ import annotations

from .errors import ReaperBridgeError

MASTER_CHAIN_PLUGINS = ["ReaEQ (Cockos)", "ReaComp (Cockos)", "ReaLimit (Cockos)"]


def apply_master_chain(project):
    master = project.master_track
    added = []
    for plugin_name in MASTER_CHAIN_PLUGINS:
        try:
            fx = master.add_fx(plugin_name)
        except ValueError as exc:
            raise ReaperBridgeError(
                f"plugin de master '{plugin_name}' não encontrado no REAPER"
            ) from exc
        added.append(fx)
    return added
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_mastering.py -v`
Expected: PASS (1 teste)

- [ ] **Step 5: Verificação manual contra o REAPER real**

Com o REAPER aberto:
```bash
uv run python -c "
from reaper_bridge.connection import get_project
from reaper_bridge.mastering import apply_master_chain
p = get_project()
fxs = apply_master_chain(p)
print([fx.name for fx in fxs])
"
```
Esperado: ReaEQ, ReaComp e ReaLimit aparecem na chain de FX da faixa mestre no REAPER, nessa ordem.

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/mastering.py tests/test_mastering.py
git commit -m "feat: aplicar chain de master padrao na faixa mestre"
```

---

## Task 7: Masterização — renderizar para .wav

**Files:**
- Modify: `reaper_bridge/mastering.py`
- Modify: `tests/fakes.py`
- Modify: `tests/test_mastering.py`

**Interfaces:**
- Consumes: `reapy.reascript_api.RPR_Main_OnCommand(command_id: int, flag: int)`; `Project.set_info_string(param_name, value)` / `Project.get_info_string(param_name)` (Task 1, fakes).
- Produces: `render_project(project, output_path: str, timeout_seconds: float = 60.0) -> str`.

- [ ] **Step 1: Acrescentar os testes (falhando)**

Adicionar ao final de `tests/test_mastering.py`:
```python
from unittest.mock import patch

import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.mastering import render_project


def test_render_project_raises_when_directory_missing(tmp_path):
    project = FakeProject([])
    missing_dir = str(tmp_path / "nao_existe" / "musica.wav")
    with pytest.raises(ReaperBridgeError, match="pasta de destino"):
        render_project(project, missing_dir)


def test_render_project_raises_for_non_wav_output(tmp_path):
    project = FakeProject([])
    output_path = str(tmp_path / "musica.mp3")
    with pytest.raises(ReaperBridgeError, match=r"\.wav"):
        render_project(project, output_path)


def test_render_project_waits_for_file_then_returns_path(tmp_path):
    project = FakeProject([])
    output_path = tmp_path / "musica.wav"

    def fake_command(command_id, flag):
        output_path.write_bytes(b"fake-audio")

    with patch(
        "reaper_bridge.mastering.reapy.reascript_api.RPR_Main_OnCommand",
        side_effect=fake_command,
    ):
        result = render_project(project, str(output_path), timeout_seconds=5)

    assert result == str(output_path)
    assert project.get_info_string("RENDER_FILE") == str(tmp_path)


def test_render_project_raises_on_timeout(tmp_path):
    project = FakeProject([])
    output_path = str(tmp_path / "musica.wav")
    with patch("reaper_bridge.mastering.reapy.reascript_api.RPR_Main_OnCommand"):
        with patch("reaper_bridge.mastering.time.sleep"):
            with pytest.raises(ReaperBridgeError, match="não terminou"):
                render_project(project, output_path, timeout_seconds=0.01)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_mastering.py -v -k render`
Expected: FAIL com `ImportError: cannot import name 'render_project'`

- [ ] **Step 3: Implementar `render_project`**

No topo de `reaper_bridge/mastering.py`, acrescentar:
```python
import os
import time

import reapy
```

Acrescentar ao final do arquivo:
```python
# Command ID da ação nativa "File: Render project, using the most recent render
# settings, auto-close render dialog". Confirmar em REAPER: Actions > Show action
# list > buscar "render project" > conferir se o Command ID mostrado bate com este
# valor antes de confiar nele em produção; se não bater, atualizar esta constante.
RENDER_ACTION_ID = 42230

DEFAULT_RENDER_TIMEOUT_SECONDS = 60.0


def render_project(
    project, output_path: str, timeout_seconds: float = DEFAULT_RENDER_TIMEOUT_SECONDS
) -> str:
    directory, filename = os.path.split(output_path)
    if not directory or not os.path.isdir(directory):
        raise ReaperBridgeError(
            f"a pasta de destino não existe: {directory or '(vazio)'}"
        )
    name, extension = os.path.splitext(filename)
    if extension.lower() != ".wav":
        raise ReaperBridgeError(
            f"apenas exportação em .wav é suportada nesta versão, recebido: {extension}"
        )
    project.set_info_string("RENDER_FILE", directory)
    project.set_info_string("RENDER_PATTERN", name)
    reapy.reascript_api.RPR_Main_OnCommand(RENDER_ACTION_ID, 0)
    deadline = time.monotonic() + timeout_seconds
    while not os.path.isfile(output_path):
        if time.monotonic() > deadline:
            raise ReaperBridgeError(
                f"o render não terminou em {timeout_seconds:.0f}s, verifique manualmente "
                f"se o arquivo foi criado em {output_path}"
            )
        time.sleep(0.5)
    return output_path
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_mastering.py -v`
Expected: PASS (5 testes)

- [ ] **Step 5: Verificação manual contra o REAPER real (confirmar o Command ID primeiro)**

1. No REAPER: **Actions → Show action list**, busque "render project". Confirme se algum item cujo nome bate com "File: Render project, using the most recent render settings, auto-close render dialog" tem Command ID `42230` (selecione a ação e veja o ID no rodapé da janela). Se o ID for diferente, atualize `RENDER_ACTION_ID` em `mastering.py` antes de continuar.
2. Configure manualmente, uma vez, as configurações de render no REAPER (**File → Render...**, formato WAV, e feche o diálogo) — isso garante que exista uma configuração "mais recente" válida para a ação reusar.
3. Rode:
   ```bash
   uv run python -c "
   from reaper_bridge.connection import get_project
   from reaper_bridge.mastering import render_project
   p = get_project()
   caminho = render_project(p, r'C:\estudos\daw_music_studio\renders\teste.wav')
   print(caminho)
   "
   ```
   (crie a pasta `renders` antes, com `mkdir renders`, já que a função exige que a pasta exista)
4. Esperado: o REAPER renderiza e fecha o diálogo sozinho, e o arquivo `renders/teste.wav` aparece no disco.

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/mastering.py tests/test_mastering.py
git commit -m "feat: renderizar projeto para wav"
```

---

## Task 8: MIDI — gerar escalas, acordes, progressões e analisar teoria

**Files:**
- Create: `reaper_bridge/midi.py`
- Test: `tests/test_midi_theory.py`

**Interfaces:**
- Consumes: `music21` (`scale`, `key`, `roman`, `note`, `chord`, `stream`); `ReaperBridgeError` (Task 1).
- Produces: `generate_scale(root: str, scale_type: str) -> list[int]`; `generate_chord(root_midi: int, quality: str) -> list[int]`; `generate_progression(key_name: str, numerals: list[str]) -> list[list[int]]`; `analyze_notes(midi_pitches: list[int]) -> str`.

- [ ] **Step 1: Escrever os testes (falhando)**

`tests/test_midi_theory.py`:
```python
import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import analyze_notes, generate_chord, generate_progression, generate_scale


def test_generate_scale_c_major_returns_expected_midi_pitches():
    pitches = generate_scale("C", "major")
    assert pitches[:8] == [48, 50, 52, 53, 55, 57, 59, 60]


def test_generate_scale_raises_for_unknown_scale_type():
    with pytest.raises(ReaperBridgeError, match="não suportada"):
        generate_scale("C", "lidian_invalido")


def test_generate_chord_c_major_returns_root_third_fifth():
    assert generate_chord(60, "major") == [60, 64, 67]


def test_generate_chord_raises_for_unknown_quality():
    with pytest.raises(ReaperBridgeError, match="não suportado"):
        generate_chord(60, "quality_invalida")


def test_generate_progression_ii_v_i_in_c_returns_three_chords():
    progression = generate_progression("C", ["ii", "V", "I"])
    assert len(progression) == 3
    assert progression[2] == [60, 64, 67]  # I em Do maior = C4 E4 G4


def test_generate_progression_raises_for_invalid_key():
    with pytest.raises(ReaperBridgeError, match="inválida"):
        generate_progression("chave_invalida_123", ["I"])


def test_analyze_notes_detects_c_major_chord():
    result = analyze_notes([60, 64, 67])
    assert "C" in result


def test_analyze_notes_raises_for_empty_input():
    with pytest.raises(ReaperBridgeError, match="nenhuma nota"):
        analyze_notes([])
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_midi_theory.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'reaper_bridge.midi'`

- [ ] **Step 3: Implementar a parte de teoria em `midi.py`**

`reaper_bridge/midi.py`:
```python
from __future__ import annotations

from music21 import chord as m21chord
from music21 import key as m21key
from music21 import note as m21note
from music21 import roman as m21roman
from music21 import scale as m21scale
from music21 import stream as m21stream

from .errors import ReaperBridgeError

SCALE_TYPES = {
    "major": m21scale.MajorScale,
    "natural_minor": m21scale.MinorScale,
    "harmonic_minor": m21scale.HarmonicMinorScale,
    "melodic_minor": m21scale.MelodicMinorScale,
    "dorian": m21scale.DorianScale,
    "mixolydian": m21scale.MixolydianScale,
}

CHORD_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
}


def generate_scale(root: str, scale_type: str) -> list[int]:
    scale_class = SCALE_TYPES.get(scale_type)
    if scale_class is None:
        raise ReaperBridgeError(
            f"escala '{scale_type}' não suportada, opções: {', '.join(SCALE_TYPES)}"
        )
    try:
        generated = scale_class(root)
        pitches = generated.getPitches(f"{root}3", f"{root}5")
    except Exception as exc:
        raise ReaperBridgeError(f"nota '{root}' inválida para gerar escala") from exc
    return [p.midi for p in pitches]


def generate_chord(root_midi: int, quality: str) -> list[int]:
    intervals = CHORD_INTERVALS.get(quality)
    if intervals is None:
        raise ReaperBridgeError(
            f"tipo de acorde '{quality}' não suportado, opções: {', '.join(CHORD_INTERVALS)}"
        )
    return [root_midi + interval for interval in intervals]


def generate_progression(key_name: str, numerals: list[str]) -> list[list[int]]:
    try:
        detected_key = m21key.Key(key_name)
    except Exception as exc:
        raise ReaperBridgeError(f"tonalidade '{key_name}' inválida") from exc
    progression = []
    for numeral in numerals:
        try:
            rn = m21roman.RomanNumeral(numeral, detected_key)
        except Exception as exc:
            raise ReaperBridgeError(
                f"grau '{numeral}' inválido para a tonalidade '{key_name}'"
            ) from exc
        progression.append([p.midi for p in rn.pitches])
    return progression


def analyze_notes(midi_pitches: list[int]) -> str:
    if not midi_pitches:
        raise ReaperBridgeError("nenhuma nota MIDI para analisar")
    notes = [m21note.Note(midi=pitch) for pitch in midi_pitches]
    detected_key = m21stream.Stream(notes).analyze("key")
    chord_obj = m21chord.Chord(notes)
    return (
        f"Tonalidade mais provável: {detected_key.tonic.name} {detected_key.mode}. "
        f"Acorde formado pelas notas: {chord_obj.pitchedCommonName}."
    )
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_midi_theory.py -v`
Expected: PASS (8 testes). Se `test_generate_scale_c_major_returns_expected_midi_pitches` ou
`test_generate_progression_ii_v_i_in_c_returns_three_chords` falharem por causa da faixa
exata de oitavas que o `music21` devolve, ajuste a asserção do teste para bater com o
valor real impresso pelo `pytest -v` (o cálculo de teoria em si — C3=48, C4=60 — está
correto; o que pode variar é o range exato de `getPitches`).

- [ ] **Step 5: Commit**

```bash
git add reaper_bridge/midi.py tests/test_midi_theory.py
git commit -m "feat: gerar escalas, acordes, progressoes e analisar notas com music21"
```

---

## Task 9: MIDI — escrever e ler o piano roll no REAPER

**Files:**
- Modify: `reaper_bridge/midi.py`
- Test: `tests/test_midi_track.py`

**Interfaces:**
- Consumes: `find_track` (Task 2); `Track.add_midi_item(start, end) -> Item`; `Item.active_take -> Take`; `Take.add_note(start, end, pitch, velocity, unit) -> Note`; `Take.notes -> list[Note]`; `Take.is_midi: bool`; `Note.pitch/start/end/velocity`.
- Produces: `write_notes_to_track(project, track_name, pitches: list[int], start=0.0, note_length=0.5, velocity=100) -> Item`; `read_notes_from_track(project, track_name) -> list[int]`.

- [ ] **Step 1: Escrever os testes (falhando)**

`tests/test_midi_track.py`:
```python
import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import read_notes_from_track, write_notes_to_track
from tests.fakes import FakeItem, FakeProject, FakeTake, FakeTrack


def test_write_notes_to_track_creates_midi_item_with_notes():
    project = FakeProject([FakeTrack("piano")])
    item = write_notes_to_track(project, "piano", [60, 64, 67], note_length=0.25)
    assert [note.pitch for note in item.active_take.notes] == [60, 64, 67]
    assert item.active_take.notes[1].start == 0.25


def test_write_notes_to_track_raises_for_empty_pitches():
    project = FakeProject([FakeTrack("piano")])
    with pytest.raises(ReaperBridgeError, match="nenhuma nota"):
        write_notes_to_track(project, "piano", [])


def test_read_notes_from_track_returns_pitches_written():
    project = FakeProject([FakeTrack("piano")])
    write_notes_to_track(project, "piano", [60, 62, 64])
    assert read_notes_from_track(project, "piano") == [60, 62, 64]


def test_read_notes_from_track_ignores_non_midi_items():
    project = FakeProject([FakeTrack("audio")])
    track = project.tracks[0]
    non_midi_item = FakeItem()
    non_midi_item.active_take = FakeTake(is_midi=False)
    track.items.append(non_midi_item)
    assert read_notes_from_track(project, "audio") == []
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_midi_track.py -v`
Expected: FAIL com `ImportError: cannot import name 'write_notes_to_track'`

- [ ] **Step 3: Implementar `write_notes_to_track` e `read_notes_from_track`**

No topo de `reaper_bridge/midi.py`, acrescentar:
```python
from .project import find_track
```

Acrescentar ao final do arquivo:
```python
def write_notes_to_track(
    project,
    track_name: str,
    pitches: list[int],
    start: float = 0.0,
    note_length: float = 0.5,
    velocity: int = 100,
):
    if not pitches:
        raise ReaperBridgeError("nenhuma nota para escrever no piano roll")
    track = find_track(project, track_name)
    end = start + note_length * len(pitches)
    item = track.add_midi_item(start=start, end=end)
    take = item.active_take
    for index, pitch_value in enumerate(pitches):
        note_start = start + index * note_length
        take.add_note(
            start=note_start,
            end=note_start + note_length,
            pitch=pitch_value,
            velocity=velocity,
            unit="seconds",
        )
    return item


def read_notes_from_track(project, track_name: str) -> list[int]:
    track = find_track(project, track_name)
    pitches = []
    for item in track.items:
        take = item.active_take
        if take is None or not take.is_midi:
            continue
        pitches.extend(note.pitch for note in take.notes)
    return pitches
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_midi_track.py -v`
Expected: PASS (4 testes)

- [ ] **Step 5: Verificação manual contra o REAPER real**

Com o REAPER aberto:
```bash
uv run python -c "
from reaper_bridge.connection import get_project
from reaper_bridge.project import create_track
from reaper_bridge.midi import write_notes_to_track, read_notes_from_track
p = get_project()
create_track(p, 'piano_teste')
write_notes_to_track(p, 'piano_teste', [60, 64, 67, 60])
print(read_notes_from_track(p, 'piano_teste'))
"
```
Esperado: uma faixa "piano_teste" aparece com um item MIDI; abrindo o piano roll dela no
REAPER (duplo clique no item), as 4 notas (C4, E4, G4, C4) aparecem na posição certa. O
comando imprime `[60, 64, 67, 60]`.

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/midi.py tests/test_midi_track.py
git commit -m "feat: escrever e ler notas MIDI no piano roll"
```

---

## Task 10: Servidor MCP

**Files:**
- Create: `mcp_server.py`
- Test: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: todas as funções de `reaper_bridge.project`, `reaper_bridge.mixing`, `reaper_bridge.mastering`, `reaper_bridge.midi`, e `get_project` (Tasks 1-9).
- Produces: 16 ferramentas MCP (`reaper_list_tracks`, `reaper_create_track`, `reaper_rename_track`, `reaper_import_audio`, `reaper_set_volume`, `reaper_set_pan`, `reaper_mute`, `reaper_solo`, `reaper_add_fx`, `reaper_set_fx_param`, `reaper_apply_master`, `reaper_render`, `reaper_generate_scale`, `reaper_generate_chord`, `reaper_generate_progression`, `reaper_write_notes`, `reaper_analyze_track`); objeto `mcp: MCPServer` no módulo.

- [ ] **Step 1: Escrever os testes (falhando)**

`tests/test_mcp_server.py`:
```python
from unittest.mock import patch

from mcp_server import (
    reaper_add_fx,
    reaper_apply_master,
    reaper_generate_scale,
    reaper_list_tracks,
    reaper_set_volume,
)
from reaper_bridge.errors import ReaperBridgeError


def test_reaper_list_tracks_returns_track_names():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.project_ops.list_tracks", return_value=["bateria", "baixo"]):
            assert reaper_list_tracks() == "Faixas: bateria, baixo"


def test_reaper_list_tracks_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", side_effect=ReaperBridgeError("REAPER fechado")):
        assert reaper_list_tracks() == "Erro: REAPER fechado"


def test_reaper_set_volume_calls_mixing_with_correct_arguments():
    fake_project = object()
    with patch("mcp_server.get_project", return_value=fake_project):
        with patch("mcp_server.mixing.set_volume") as mock_set_volume:
            result = reaper_set_volume("voz", 3.0)
    mock_set_volume.assert_called_once_with(fake_project, "voz", 3.0)
    assert "3.0" in result


def test_reaper_apply_master_lists_added_plugins():
    fake_fx = type("FakeFX", (), {"name": "ReaEQ (Cockos)"})()
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.mastering.apply_master_chain", return_value=[fake_fx]):
            assert "ReaEQ" in reaper_apply_master()


def test_reaper_generate_scale_returns_pitches_as_text():
    with patch("mcp_server.midi.generate_scale", return_value=[60, 62, 64]):
        assert "[60, 62, 64]" in reaper_generate_scale("C", "major")


def test_reaper_add_fx_reports_success():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.mixing.add_fx"):
            assert "ReaEQ" in reaper_add_fx("voz", "ReaEQ (Cockos)")
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'mcp_server'`

- [ ] **Step 3: Implementar `mcp_server.py`**

```python
from __future__ import annotations

from mcp.server import MCPServer

from reaper_bridge import mastering, midi, mixing
from reaper_bridge import project as project_ops
from reaper_bridge.connection import get_project
from reaper_bridge.errors import ReaperBridgeError

mcp = MCPServer("reaper-copilot")


def _run(operation):
    try:
        return operation()
    except ReaperBridgeError as exc:
        return f"Erro: {exc}"


@mcp.tool()
def reaper_list_tracks() -> str:
    """Lista as faixas do projeto REAPER atualmente aberto."""
    def operation():
        names = project_ops.list_tracks(get_project())
        return "Faixas: " + (", ".join(names) if names else "(nenhuma)")
    return _run(operation)


@mcp.tool()
def reaper_create_track(name: str) -> str:
    """Cria uma nova faixa vazia no projeto REAPER com o nome dado."""
    def operation():
        project_ops.create_track(get_project(), name)
        return f"Faixa '{name}' criada."
    return _run(operation)


@mcp.tool()
def reaper_rename_track(name: str, new_name: str) -> str:
    """Renomeia uma faixa existente."""
    def operation():
        project_ops.rename_track(get_project(), name, new_name)
        return f"Faixa '{name}' renomeada para '{new_name}'."
    return _run(operation)


@mcp.tool()
def reaper_import_audio(file_path: str, track_name: str | None = None) -> str:
    """Importa um arquivo de áudio como uma nova faixa no projeto REAPER."""
    def operation():
        track = project_ops.import_audio(get_project(), file_path, track_name)
        return f"Áudio importado na faixa '{track.name}'."
    return _run(operation)


@mcp.tool()
def reaper_set_volume(track_name: str, db: float) -> str:
    """Ajusta o volume (em dB) de uma faixa."""
    def operation():
        mixing.set_volume(get_project(), track_name, db)
        return f"Volume da faixa '{track_name}' ajustado para {db} dB."
    return _run(operation)


@mcp.tool()
def reaper_set_pan(track_name: str, pan: float) -> str:
    """Ajusta o pan (-1.0 esquerda a 1.0 direita) de uma faixa."""
    def operation():
        mixing.set_pan(get_project(), track_name, pan)
        return f"Pan da faixa '{track_name}' ajustado para {pan}."
    return _run(operation)


@mcp.tool()
def reaper_mute(track_name: str, muted: bool) -> str:
    """Muta ou desmuta uma faixa."""
    def operation():
        mixing.set_mute(get_project(), track_name, muted)
        return f"Faixa '{track_name}' {'mutada' if muted else 'desmutada'}."
    return _run(operation)


@mcp.tool()
def reaper_solo(track_name: str, solo: bool) -> str:
    """Ativa ou desativa solo numa faixa."""
    def operation():
        mixing.set_solo(get_project(), track_name, solo)
        return f"Solo da faixa '{track_name}' {'ativado' if solo else 'desativado'}."
    return _run(operation)


@mcp.tool()
def reaper_add_fx(track_name: str, fx_name: str) -> str:
    """Adiciona um plugin (FX) a uma faixa, pelo nome exato do plugin no REAPER."""
    def operation():
        mixing.add_fx(get_project(), track_name, fx_name)
        return f"Plugin '{fx_name}' adicionado à faixa '{track_name}'."
    return _run(operation)


@mcp.tool()
def reaper_set_fx_param(track_name: str, fx_name: str, param_name: str, value: float) -> str:
    """Ajusta um parâmetro (valor normalizado 0.0-1.0) de um plugin numa faixa."""
    def operation():
        mixing.set_fx_param(get_project(), track_name, fx_name, param_name, value)
        return f"Parâmetro '{param_name}' de '{fx_name}' ajustado para {value}."
    return _run(operation)


@mcp.tool()
def reaper_apply_master() -> str:
    """Aplica a chain de masterização padrão (EQ, compressor, limiter) na faixa mestre."""
    def operation():
        fxs = mastering.apply_master_chain(get_project())
        return "Master aplicado: " + ", ".join(fx.name for fx in fxs)
    return _run(operation)


@mcp.tool()
def reaper_render(output_path: str) -> str:
    """Renderiza o projeto para um arquivo .wav no caminho indicado."""
    def operation():
        path = mastering.render_project(get_project(), output_path)
        return f"Render concluído: {path}"
    return _run(operation)


@mcp.tool()
def reaper_generate_scale(root: str, scale_type: str) -> str:
    """Gera uma escala (ex.: root='C', scale_type='major') como lista de notas MIDI."""
    def operation():
        pitches = midi.generate_scale(root, scale_type)
        return f"Notas MIDI da escala: {pitches}"
    return _run(operation)


@mcp.tool()
def reaper_generate_chord(root_midi: int, quality: str) -> str:
    """Gera um acorde a partir de uma nota raiz MIDI e um tipo (major, minor, dominant7, ...)."""
    def operation():
        pitches = midi.generate_chord(root_midi, quality)
        return f"Notas MIDI do acorde: {pitches}"
    return _run(operation)


@mcp.tool()
def reaper_generate_progression(key_name: str, numerals: list[str]) -> str:
    """Gera uma progressão de acordes (graus em algarismo romano) numa tonalidade."""
    def operation():
        progression = midi.generate_progression(key_name, numerals)
        return f"Progressão gerada: {progression}"
    return _run(operation)


@mcp.tool()
def reaper_write_notes(track_name: str, pitches: list[int], note_length: float = 0.5) -> str:
    """Escreve uma sequência de notas MIDI no piano roll de uma faixa."""
    def operation():
        midi.write_notes_to_track(get_project(), track_name, pitches, note_length=note_length)
        return f"{len(pitches)} notas escritas na faixa '{track_name}'."
    return _run(operation)


@mcp.tool()
def reaper_analyze_track(track_name: str) -> str:
    """Lê as notas MIDI de uma faixa e devolve uma análise teórica (tonalidade/acorde)."""
    def operation():
        pitches = midi.read_notes_from_track(get_project(), track_name)
        return midi.analyze_notes(pitches)
    return _run(operation)


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Nota: as ferramentas não testadas explicitamente no Step 1 (`reaper_create_track`,
`reaper_rename_track`, `reaper_import_audio`, `reaper_set_pan`, `reaper_mute`,
`reaper_solo`, `reaper_set_fx_param`, `reaper_render`, `reaper_generate_chord`,
`reaper_generate_progression`, `reaper_write_notes`, `reaper_analyze_track`) seguem o
mesmo padrão `_run(operation)` já coberto pelos testes escritos — a verificação manual do
Step 5 é o que confirma que cada uma individualmente está correta.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: PASS (6 testes)

- [ ] **Step 5: Verificação manual com o cliente de desenvolvimento do MCP**

Com o REAPER aberto:
```bash
uv run mcp dev mcp_server.py
```
Isso abre um cliente de desenvolvimento do SDK do MCP no navegador. Chame manualmente
pelo menos 3 ferramentas (por exemplo `reaper_list_tracks`, `reaper_create_track` com
`name="verificação_mcp"`, e `reaper_generate_scale` com `root="C"`, `scale_type="major"`)
e confirme que a resposta bate com o que aparece no REAPER e que nenhuma chamada trava.

- [ ] **Step 6: Commit**

```bash
git add mcp_server.py tests/test_mcp_server.py
git commit -m "feat: servidor MCP expondo as ferramentas do reaper_bridge"
```

---

## Task 11: Registro no Claude Code e checklist de smoke test manual

**Files:**
- Create: `.mcp.json`
- Modify: `README.md`

**Interfaces:**
- Consumes: `mcp_server.py` (Task 10).
- Produces: nada consumido por outras tasks (task final).

- [ ] **Step 1: Criar `.mcp.json`**

```json
{
  "mcpServers": {
    "reaper-copilot": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"]
    }
  }
}
```

- [ ] **Step 2: Escrever o `README.md`**

```markdown
# reaper-copilot

IA (Claude Code) controlando o REAPER via `reapy` + um servidor MCP local, para mixar,
masterizar e gerar/analisar MIDI no piano roll a partir de comandos em linguagem natural.
Desenho completo em
`docs/superpowers/specs/2026-09-26-reaper-copilot-design.md`.

## Setup

1. Instale o REAPER (https://www.reaper.fm/download.php) e abra-o pelo menos uma vez.
2. Habilite Python no ReaScript: **Options → Preferences → Plug-ins → ReaScript**,
   marque "Enable Python for use with ReaScript" e aponte o caminho customizado do
   Python para a instalação do `uv` (`uv python find`, ou veja o `.venv/pyvenv.cfg`
   deste projeto em `home = ...`).
3. `uv sync`
4. Com o REAPER aberto: `uv run python -c "import reapy; reapy.configure_reaper()"`
   (reinicie o REAPER se ele pedir).
5. Verifique: `uv run python -c "import reapy; print(reapy.Project())"` deve imprimir o
   projeto ativo sem erro.
6. Reinicie o Claude Code neste diretório (ou rode `/mcp` para recarregar) — o servidor
   `reaper-copilot` do `.mcp.json` deve aparecer na lista de servidores MCP conectados.

## Testes automatizados

`uv run pytest` — roda todos os testes de `reaper_bridge` e `mcp_server.py` com o
REAPER mockado (não precisa do REAPER aberto).

## Checklist de smoke test manual (precisa do REAPER aberto)

Não dá para automatizar isso em CI — é uma verificação ponta a ponta contra o REAPER de
verdade. Rode pelo Claude Code, num projeto REAPER vazio:

- [ ] "Lista as faixas do projeto" → responde "(nenhuma)" ou as faixas existentes.
- [ ] "Cria uma faixa chamada bateria" → aparece uma faixa nova no REAPER.
- [ ] "Importa esse áudio: `<caminho de um .wav de teste>`" → aparece uma nova faixa com
      o áudio, começando em 0:00.
- [ ] "Aumenta o volume da faixa bateria para -3dB" e "muda o pan para a esquerda" →
      o fader e o pan se movem no REAPER.
- [ ] "Adiciona um ReaEQ na faixa bateria" → o plugin aparece na chain de FX da faixa.
- [ ] "Aplica a chain de master" → ReaEQ, ReaComp e ReaLimit aparecem na faixa mestre.
- [ ] "Renderiza o projeto para `<pasta>\teste.wav`" → o arquivo aparece na pasta.
- [ ] "Gera uma escala de Dó maior no piano roll da faixa piano" → as notas aparecem no
      piano roll dessa faixa.
- [ ] "Analisa o que eu toquei nessa faixa" (depois de tocar/gravar algo com um teclado
      MIDI conectado ao REAPER numa faixa MIDI) → devolve uma análise de
      tonalidade/acorde coerente com o que foi tocado.
```

- [ ] **Step 3: Verificar que o Claude Code carrega o servidor**

Reinicie a sessão do Claude Code (ou rode `/mcp`) dentro de `C:\estudos\daw_music_studio`
e confirme que `reaper-copilot` aparece como servidor MCP conectado, com as 16
ferramentas listadas.

- [ ] **Step 4: Rodar o checklist de smoke test manual**

Percorra os itens do checklist do `README.md` acima, um a um, conversando com o Claude
Code (não rodando scripts Python direto) — é o teste real de que a integração ponta a
ponta funciona do jeito que o usuário vai usar.

- [ ] **Step 5: Commit**

```bash
git add .mcp.json README.md
git commit -m "docs: registrar servidor MCP no Claude Code e checklist de smoke test"
```
