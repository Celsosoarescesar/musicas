# Auditoria de sessão REAPER (reaper-copilot) — primeira fase de paridade com o ReaAssist

## Contexto

O usuário cogitou instalar o ReaAssist (extensão Lua/ReaImGui que roda
dentro do REAPER, oferecendo um chat que lê o estado da sessão e executa
ações via LLM próprio). Decidiu não instalar — ele já conversa com o
Claude Code (aqui) para controlar o REAPER, através do `reaper-copilot`
(MCP server existente, 17 tools, ver
`docs/superpowers/specs/2026-09-26-reaper-copilot-design.md`).

**Diferença arquitetural chave:** o ReaAssist gera e executa Lua *dentro*
do REAPER porque é a única forma de agir que uma extensão embutida tem.
O `reaper-copilot` já age *de fora*, via `reapy`. Não há motivo para
replicar o pipeline do ReaAssist (gerar código → escanear por padrões
perigosos → confirmar → rodar com undo) — cada capacidade do ReaAssist
que faz sentido aqui se torna uma função Python comum em
`reaper_bridge/`, mais uma tool MCP. O "loop comando em linguagem
natural → chamada de tool" já existe: é esta conversa.

O conjunto de features do ReaAssist é grande demais para uma spec só, e
foi dividido em blocos (ver conversa de brainstorming). Esta spec cobre
o primeiro bloco, escolhido pelo usuário por ser baixo risco (somente
leitura) e servir de base para os próximos: **auditoria estrutural de
sessão**.

## Fora de escopo (deste documento)

- **Análise de pico/LUFS de áudio** (itens selecionados) — adiada para
  um bloco próprio; exige ler amostras de áudio de verdade (não só
  metadados), provável necessidade de `pyloudnorm` ou renderização
  temporária, complexidade bem diferente do resto desta spec.
- **Routing/buses** (sidechain, parallel returns, reverb compartilhado,
  drum bus) — bloco futuro, estes modificam a sessão; esta spec é
  somente leitura.
- **Edição de MIDI** (humanizar, corrigir sobreposições, transpor,
  velocity em lote) — bloco futuro, estende `reaper_bridge/midi.py`.
- **Markers/regions, notas de faixa, sistema de plugin preferido,
  cache de parâmetros, preferências persistentes entre sessões** —
  blocos futuros, não endereçados aqui.
- **Qualquer geração/execução de código Lua arbitrário** — decisão
  arquitetural: não será replicado (ver "Contexto" acima). Sempre que
  uma capacidade do ReaAssist fizer sentido, ela se torna uma função
  Python testável em `reaper_bridge/`, não um script gerado.

## Arquitetura

```
REAPER (aberto, sessão ao vivo)
   ^
   | reapy
   |
reaper_bridge/audit.py   (novo módulo: 5 verificações estruturais +
   |                      resumo de uma faixa — tudo somente leitura,
   |                      devolve dados estruturados, não strings)
   |
mcp_server.py            (duas tools novas: reaper_audit_session,
   |                      reaper_track_summary — formatam o resultado
   |                      de audit.py em texto legível em português)
   |
Claude Code               (você pede "audita a sessão" ou "resume a
                           faixa baixo"; eu chamo a tool certa)
```

Segue exatamente o padrão já estabelecido em `reaper_bridge/project.py`
e `mixing.py`: cada função pública recebe `project` como parâmetro,
toda chamada `reapy` que pode falhar fica protegida e vira
`ReaperBridgeError` em caso de erro. Novidade desta spec, formalizando
uma convenção que ainda não existia explicitamente: **funções de
`reaper_bridge` devolvem dados estruturados (listas/dicts), nunca
strings formatadas** — a formatação em português para o usuário final é
responsabilidade exclusiva de `mcp_server.py`. As tools existentes já
seguem isso informalmente; esta spec só o torna explícito para o código
novo.

## Componentes

### `reaper_bridge/audit.py` (novo módulo)

Cinco verificações estruturais, cada uma uma função pura (recebe
`project`, devolve uma lista):

- `find_armed_tracks(project) -> list[str]` — nomes das faixas com
  `track.get_info_value("I_RECARM") == 1.0`.
- `find_muted_tracks(project) -> list[str]` — nomes das faixas com
  `track.is_muted`.
- `find_empty_tracks(project) -> list[str]` — nomes das faixas com
  `track.n_items == 0`.
- `find_bypassed_fx(project) -> list[tuple[str, str]]` — pares
  `(nome_da_faixa, nome_do_plugin)` para cada FX com
  `fx.is_enabled is False` (bypassed).
- `find_multi_destination_sends(project) -> list[tuple[str, list[str]]]`
  — pares `(nome_da_faixa, [nomes_dos_destinos])` para cada faixa com
  `track.n_sends > 1`.

Todas as cinco ignoram a master track (`project.master_track`) — ela
não participa da lista `project.tracks` iterada por essas funções (
confirmado ao vivo: `project.tracks` já exclui a master).

Mais uma função, de resumo de uma faixa específica:

- `summarize_track(project, track_name) -> dict` — levanta
  `ReaperBridgeError` se `track_name` não existir (reaproveitando o
  helper de busca por nome já usado em `mixing.py`/`project.py`).
  Devolve:
  ```python
  {
      "name": str,
      "color": tuple[int, int, int],      # ex.: (0, 0, 0) = cor padrão do tema
      "depth": int,                        # nivel de nesting (0 = nivel superior, 1 = dentro de uma pasta, etc.) -- NAO e o mesmo que I_FOLDERDEPTH
      "is_muted": bool,
      "is_armed": bool,
      "fx": [{"name": str, "enabled": bool}, ...],
      "sends": [{"dest": str, "volume": float}, ...],
  }
  ```

Cada função envolve suas chamadas `reapy` (`get_info_value`,
`is_muted`, `n_items`, `fxs`, `is_enabled`, `n_sends`, `sends`,
`dest_track.name`, `color`, `depth`) no mesmo padrão
`try/except Exception as exc: raise ReaperBridgeError(...) from exc`
usado no resto de `reaper_bridge/`.

### `mcp_server.py` (duas tools novas)

- **`reaper_audit_session() -> str`** — chama as cinco funções de
  `find_*`, monta um checklist em português:
  ```
  Auditoria da sessão:
    ⚠ 2 faixas armadas para gravação: Voz, Guitarra
    ⚠ 1 faixa mutada: Baixo
    ✓ nenhuma faixa vazia
    ⚠ 1 FX bypassed: Piano → ReaEQ
    ✓ nenhuma faixa com sends para múltiplos destinos
  ```
  Cada categoria vazia usa "✓" com a frase "nenhum(a) ... encontrado";
  cada categoria com achados usa "⚠" e lista os nomes.
- **`reaper_track_summary(track_name: str) -> str`** — chama
  `summarize_track`, formata o dict num texto com FX chain, sends, cor,
  pasta, mute/arm — mesmo estilo de texto plano em português das outras
  tools (`reaper_apply_master`, `reaper_analyze_track`, etc.).

Ambas seguem o padrão `_run()` já existente (lock, captura
`ReaperBridgeError` → `"Erro: ..."`, backstop genérico).

## Fluxo

1. Você pede ("audita a sessão" ou "resume a faixa Baixo").
2. Eu chamo `reaper_audit_session` ou `reaper_track_summary` com os
   parâmetros certos.
3. A tool adquire o `_REAPER_LOCK`, chama `audit.py`, que lê o estado
   via `reapy` — nada é modificado, só leitura.
4. A tool formata o resultado em português e eu te devolvo o checklist
   ou o resumo.

## Tratamento de erros

- Qualquer leitura `reapy` que falhar (ex.: REAPER fechado no meio da
  chamada) vira `ReaperBridgeError` com mensagem acionável, igual ao
  resto de `reaper_bridge/`.
- `summarize_track` com nome de faixa inexistente: erro citando o nome
  pedido e as faixas disponíveis no projeto atual (mesmo padrão de
  `mixing.py`).
- Nenhuma tool deixa uma exceção crua chegar ao Claude Code.

## Testes

Sem precisar do REAPER aberto, via `tests/fakes.py` (estendido):

- `FakeTrack` ganha `color` (tupla, default `(0, 0, 0)`), `depth`
  (int, default `0`), e suporte a `get_info_value`/`set_info_value`
  para simular `I_RECARM` (reaproveitando o padrão que `FakeProject` já
  usa para `get_info_string`/`set_info_string`).
- `FakeFX` ganha `is_enabled` (default `True`) e um método `disable()`
  que seta `is_enabled = False` (espelhando a API real confirmada ao
  vivo: `fx.disable()` → `fx.is_enabled` passa a `False`).
- Novo `FakeSend` (classe simples: `dest_track`, `volume`) e
  `FakeTrack.add_send(dest_track, volume=0.0)` que cria um `FakeSend` e
  o adiciona a `FakeTrack.sends` (lista nova no construtor).
- Cada função de `audit.py` ganha pelo menos dois testes: um caso com
  achado (ex.: uma faixa armada entre outras não-armadas) e um caso
  limpo (lista vazia) — mesmo estilo dos testes existentes de
  `mixing.py`/`project.py` em `tests/`.
- `summarize_track`: um teste do dict completo (faixa com FX bypassed,
  send, cor e pasta não-default) e um teste do erro de faixa
  inexistente.
- `mcp_server.py`: testes de formatação (dict/listas de `audit.py`
  mockados → string esperada), mesmo padrão dos testes de despacho já
  existentes para as outras tools.

## Verificação ao vivo feita antes desta spec

Confirmado com REAPER aberto, criando e removendo faixas temporárias
(`TEMP_AUDIT_PROBE`, `TEMP_AUDIT_DEST`):

- `track.color` → tupla `(0, 0, 0)` por padrão (cor do tema, não
  "preto" literal).
- `track.depth` → `0` por padrão.
- `track.get_info_value("I_RECARM")` → `0.0`/`1.0` (float, não bool).
- `fx.is_enabled` → `True` por padrão; `fx.disable()` → `is_enabled`
  vira `False`.
- `track.n_sends` e `track.sends[i].dest_track.name` → routing básico
  funciona como esperado.
- `track.n_items` → `0` numa faixa recém-criada sem itens.

## Próximos blocos (fora do escopo deste documento)

Pela ordem discutida no brainstorming, ainda ficam para specs futuras:
pico/LUFS de áudio, routing/buses, edição de MIDI, edição de item de
áudio, markers/regions, gestão de plugins/FX, preferências
persistentes.
