# Sends, buses e pastas de faixas (reaper-copilot) — segundo bloco de paridade com o ReaAssist

## Contexto

Continuação da série de blocos extraída das features do ReaAssist (ver
`docs/superpowers/specs/2026-10-02-reaper-audit-design.md` pra o
raciocínio arquitetural geral: nenhum pipeline de geração/execução de Lua
é replicado, cada capacidade vira uma função Python testável em
`reaper_bridge/`). O primeiro bloco (auditoria estrutural) já foi
implementado e mergeado. Este é o segundo: **sends, buses de roteamento e
agrupamento de faixas em pastas** — a parte das features "Routing
Configuration" e "Track Creation and Organization" do ReaAssist que não
depende de plugins específicos.

## Fora de escopo (deste documento)

- **Sidechain compression** — decisão explícita do brainstorming: precisa
  de pesquisa ao vivo própria sobre o roteamento de FX do ReaComp
  (detector input), que é uma categoria de problema diferente (pin
  mapping de plugin, não roteamento de faixa). Fica pra uma spec futura.
- **Edição de MIDI, edição de item de áudio, markers/regions, gestão de
  plugins/FX, preferências persistentes** — outros blocos da mesma série,
  não endereçados aqui.

## Arquitetura

```
reaper_bridge/routing.py   (novo módulo: create_send, route_tracks_to_bus,
   |                        group_into_folder)
   |
   +-- reaper_bridge/project.py   (reaproveita find_track, get_or_create_track)
   +-- reaper_bridge/mixing.py    (reaproveita _db_to_linear)
   |
mcp_server.py               (tools novas expondo as três funções)
```

Mesma convenção dos módulos existentes: cada função pública recebe
`project` como primeiro parâmetro, toda chamada `reapy` que pode falhar
fica protegida e vira `ReaperBridgeError`. `_db_to_linear` (já existe em
`mixing.py`, usado por `set_volume`) é importado e reaproveitado, não
duplicado — a conversão dB→ganho linear é idêntica para volume de faixa e
volume de send (ambos confirmados ao vivo: `track.volume` e `send.volume`
são ganho linear, default `1.0` = 0dB).

## Componentes

### `reaper_bridge/routing.py` (novo módulo)

- **`create_send(project, source_track_name, dest_track_name, level_db=0.0) -> send`**
  — encontra as duas faixas via `find_track`. Se já existir um send de
  `source` para `dest` (comparando `send.dest_track.name` nos sends
  existentes da faixa de origem), **atualiza o volume** desse send em vez
  de criar um novo — evita sends duplicados quando o mesmo pedido é feito
  duas vezes (ex.: usuário ajusta o nível de um send que já existe).
  Senão, cria um novo via `source_track.add_send(dest_track)` e define o
  volume.
- **`route_tracks_to_bus(project, bus_name, source_track_names, level_db=0.0) -> track`**
  — garante que a faixa-bus existe (via `get_or_create_track`, que já
  trata nome ambíguo/duplicado) e chama `create_send` pra cada faixa de
  origem, pra essa bus, no nível pedido. Cobre "shared reverb return" e
  "drum bus" do ReaAssist — a bus pode já existir (sends adicionais só se
  somam aos que já existem) ou ser criada agora.
- **`group_into_folder(project, parent_name, child_track_names) -> track`**
  — garante que a faixa-pai existe (via `get_or_create_track`). Seleciona
  **apenas** as faixas-filhas nomeadas (`find_track` pra cada uma,
  `track.is_selected = True` só nessas — nunca um "deselect all" que
  tocaria em faixas que o usuário possa ter selecionado por conta
  própria). Calcula `target = pai.index + 1` (lido na hora, depois de
  resolver a faixa-pai) e chama
  `reapy.reascript_api.ReorderSelectedTracks(target, 1)` — confirmado ao
  vivo: isso move as faixas selecionadas pra logo depois do pai e o
  REAPER mesmo marca `I_FOLDERDEPTH` corretamente (pai=1, filhas do meio
  inalteradas, última filha=-1 fechando a pasta). Nenhum cálculo manual de
  `I_FOLDERDEPTH` é necessário.

Cada função envolve suas chamadas `reapy` no mesmo padrão
`try/except Exception as exc: raise ReaperBridgeError(...) from exc` do
resto de `reaper_bridge/`.

### `mcp_server.py` (três tools novas)

- **`reaper_create_send(source_track_name: str, dest_track_name: str, level_db: float = 0.0) -> str`**
- **`reaper_route_to_bus(bus_name: str, source_track_names: list[str], level_db: float = 0.0) -> str`**
- **`reaper_group_into_folder(parent_name: str, child_track_names: list[str]) -> str`**

Todas seguem o padrão `_run()` já existente (lock, captura
`ReaperBridgeError` → `"Erro: ..."`, backstop genérico), formatando o
resultado em português (ex.: `"Send criado: 'Bateria' -> 'Reverb Bus'
(-6.0 dB)"`, `"3 faixas roteadas para a bus 'Reverb Bus'"`,
`"Pasta 'Ritmo' criada com 2 faixa(s)"`).

## Fluxo

1. Você pede ("cria uma bus de reverb e manda bateria e voz pra ela com
   -6dB", "agrupa bateria e baixo numa pasta chamada Ritmo").
2. Eu chamo a tool MCP certa.
3. A tool adquire o `_REAPER_LOCK`, chama `routing.py`, que executa via
   `reapy` — a mudança acontece ao vivo, na tela do REAPER.
4. Eu confirmo o que foi feito (ou repito o erro de forma clara).

## Tratamento de erros

- Faixa de origem/destino/pai inexistente: `find_track`/`get_or_create_track`
  já tratam isso com mensagem citando faixas disponíveis.
- Falha de leitura/escrita do `reapy` (ex.: REAPER fechado no meio da
  chamada): vira `ReaperBridgeError` com mensagem acionável, igual ao
  resto de `reaper_bridge/`.
- Nenhuma tool deixa uma exceção crua chegar ao Claude Code.

## Testes

- `tests/fakes.py`: nenhuma extensão nova é necessária — `FakeTrack` já
  tem `is_selected`, `add_send`, `sends`; `FakeProject` já tem `tracks`.
  A chamada de baixo nível `reapy.reascript_api.ReorderSelectedTracks`
  **não é simulada por um fake** — ela é mockada diretamente nos testes
  de `group_into_folder`, seguindo exatamente o precedente já
  estabelecido em `reaper_bridge/project.py`'s `import_audio` (que chama
  `reapy.reascript_api.InsertMedia` do mesmo jeito e é testado via
  `patch("reaper_bridge.project.reapy.reascript_api.InsertMedia")` em
  `tests/test_project.py`). `routing.py` importa `reapy` no topo do
  arquivo e chama `reapy.reascript_api.ReorderSelectedTracks(...)`
  diretamente; os testes usam
  `patch("reaper_bridge.routing.reapy.reascript_api.ReorderSelectedTracks")`.
- `create_send`: teste de criação nova (nenhum send prévio), teste de
  atualização (já existe um send pra mesma faixa de destino — volume
  muda, nenhum send novo é criado, `len(track.sends)` não aumenta).
- `route_tracks_to_bus`: teste criando a bus do zero, teste reaproveitando
  uma bus já existente (nenhuma faixa nova criada, só sends adicionados).
- `group_into_folder`: teste verificando que **apenas** as faixas-filhas
  nomeadas tiveram `is_selected` setado pra `True` (outras faixas do
  projeto, incluindo uma não mencionada no pedido, continuam com seu
  `is_selected` original) e que `ReorderSelectedTracks` foi chamado com o
  `target`/`makePrevFolder` corretos (mockado, não precisa de REAPER
  aberto).
- `mcp_server.py`: testes de formatação (mockando as funções de
  `routing.py`), mesmo padrão dos testes de despacho já existentes.

## Verificação ao vivo feita antes desta spec

Confirmado com REAPER aberto, usando faixas temporárias sempre criadas no
fim da lista (`project.n_tracks` como índice de inserção, nunca em
posições baixas que deslocariam faixas reais) e seleção restrita só às
faixas temporárias (nunca um "deselect all" que tocaria em faixas reais):

- `send.volume` é ganho linear, default `1.0` (0dB), idêntico a
  `track.volume` — mesma conversão `_db_to_linear` se aplica.
- `reapy.reascript_api.ReorderSelectedTracks(beforeTrackIdx, makePrevFolder)`
  move as faixas **selecionadas** pra ocupar posições consecutivas a
  partir do índice absoluto `beforeTrackIdx` (não é "antes da posição
  atual de uma faixa específica" — é um índice absoluto no array de
  faixas no momento da chamada). Com `makePrevFolder=1`, a faixa que fica
  imediatamente antes do bloco movido recebe `I_FOLDERDEPTH=1` (abre
  pasta) e a última faixa do bloco movido recebe `I_FOLDERDEPTH=-1`
  (fecha pasta) — confirmado com `pai.index + 1` como `beforeTrackIdx`,
  resultando exatamente na pasta esperada.
- **Incidente durante a verificação (corrigido, documentado em
  `feedback_reapy_live_verification_side_effects` na memória):** uma
  primeira tentativa dessa verificação usou um "deselect all" que
  indesejadamente afetou uma faixa real do projeto do usuário (marcou
  `I_FOLDERDEPTH=1` numa faixa chamada "3_master" que não fazia parte do
  teste). Corrigido na hora e revertido. A segunda tentativa, restrita
  apenas às faixas temporárias recém-criadas, funcionou corretamente sem
  tocar em nenhuma faixa real — esse é o padrão que `group_into_folder`
  deve seguir (nunca selecionar/deselecionar faixas fora do pedido do
  usuário).

## Próximos blocos (fora do escopo deste documento)

Pela ordem discutida: edição de MIDI, edição de item de áudio (+
pico/LUFS, adiado do primeiro bloco), markers/regions, gestão de
plugins/FX, preferências persistentes. Sidechain compression fica como
extensão futura deste bloco, não uma spec própria, já que compartilha a
base de `create_send`.
