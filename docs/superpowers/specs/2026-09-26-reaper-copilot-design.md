# REAPER Copilot — IA controlando o REAPER via Claude Code

## Contexto

Já existe, em `music_studio/` (repositório separado), toda a esteira de
geração musical por IA: ACE-Step gera a música, Demucs separa as faixas
(vocals/drums/bass/other), e há uma masterização básica automática. O
resultado de tudo isso são arquivos `.wav` (música completa + stems) em
`music_studio/projects/ace-step-orchestrator/output/`.

O que falta, e é o objetivo deste projeto: pegar esse material e
**trabalhar a música dentro do REAPER** (um DAW de verdade), com uma IA
(Claude Code, aqui mesmo no chat) controlando o REAPER por comando em
linguagem natural — criar faixas, importar áudio, mixar, aplicar master,
renderizar — além de usar o piano roll do REAPER como ferramenta de
aprendizado musical (gerar e analisar exercícios com teoria via
`music21`).

Este é um projeto novo e independente, em `C:\estudos\daw_music_studio`
(fora de `music_studio/`, com seu próprio ambiente virtual `uv` e seu
próprio repositório git), de nome `reaper-copilot`.

## Fora de escopo

- Reimplementar geração de música, separação de faixas ou masterização
  automática — isso já existe em `music_studio/` e continua sendo usado
  como fonte dos arquivos de áudio.
- Gravação de voz/MIDI pelo navegador — a gravação acontece dentro do
  próprio REAPER (ele já sabe fazer isso), não é responsabilidade deste
  projeto.
- Uma interface de chat própria (web ou CLI) — o MVP conversa comigo,
  aqui no Claude Code. Uma integração futura com o chat web do
  `music-studio` é possível reaproveitando o mesmo pacote
  `reaper_bridge`, mas fica para um spec futuro, se/quando fizer falta.

## Arquitetura

```
REAPER (aberto, sessão ao vivo)
   ^
   | reapy (biblioteca Python; fala com o REAPER via um servidor
   |        socket instalado dentro dele)
   |
reaper_bridge/  (pacote Python: a lógica de projeto/mixagem/
   |             masterização/piano-roll)
   |
mcp_server.py   (servidor MCP; expõe as funções do reaper_bridge
   |             como ferramentas)
   |
Claude Code     (você conversa comigo; eu escolho as ferramentas
                 certas a partir do que você pede)
```

`reapy` foi escolhido em vez de escrever um protocolo próprio em
ReaScript (Lua) porque já resolve a comunicação com o REAPER de forma
madura — API Python de alto nível sobre projetos/faixas/FX/itens. MCP
foi escolhido porque é o jeito padrão de dar ferramentas novas ao Claude
Code, sem precisar construir nem manter um chatbot próprio agora.

## Componentes

### `reaper_bridge/` (pacote Python)

- **`connection.py`** — conecta ao REAPER via `reapy`; traduz falhas de
  conexão (REAPER fechado, `reapy` não configurado) numa exceção própria
  (`ReaperBridgeError`) com mensagem clara para o usuário final.
- **`project.py`** — criar projeto, importar um arquivo de áudio como
  nova faixa, criar/renomear faixas, listar faixas existentes.
- **`mixing.py`** — volume e pan por faixa, mute/solo, adicionar FX
  (EQ, compressor, reverb) numa faixa com parâmetros básicos.
- **`mastering.py`** — aplicar uma chain de master pré-definida na
  faixa mestre (EQ + compressor + limiter, valores sensatos por
  padrão), normalizar, renderizar o projeto para um `.wav` final.
- **`midi.py`** — usa `music21` como motor de teoria musical:
  - gerar uma escala, um acorde ou uma progressão (ex.: "ii-V-I em Sol")
    como notas MIDI, escritas diretamente no piano roll de uma faixa;
  - ler as notas MIDI de uma faixa (o que o usuário tocou/gravou) e
    devolver uma análise em texto (acorde/escala mais próxima, notas
    fora do esperado) usando as ferramentas de análise do `music21`.

Toda função pública de `reaper_bridge` levanta `ReaperBridgeError` em
vez de deixar vazar exceções cruas do `reapy` — mensagens sempre
acionáveis (ex.: "faixa 'voz' não existe, faixas disponíveis:
baixo, bateria, master").

### `mcp_server.py`

Servidor MCP (transporte stdio) com uma ferramenta por ação, cada uma
um wrapper fino sobre `reaper_bridge`:

`reaper_create_project`, `reaper_import_audio`, `reaper_create_track`,
`reaper_list_tracks`, `reaper_set_volume`, `reaper_set_pan`,
`reaper_mute_solo`, `reaper_add_fx`, `reaper_apply_master`,
`reaper_render`, `reaper_generate_exercise`, `reaper_analyze_midi`.

Cada ferramenta devolve um resultado estruturado (o que foi feito, ou o
erro de `ReaperBridgeError`) — nunca deixa uma exceção não tratada
derrubar o servidor.

### `.mcp.json`

Registra `mcp_server.py` (rodado via `uv run python mcp_server.py`) para
o Claude Code carregar automaticamente quando o diretório do projeto
estiver aberto.

## Fluxo

1. Você pede em linguagem natural ("cria uma faixa de baixo e importa
   esse stem", "aumenta 3dB a voz", "aplica master e exporta", "me dá
   uma progressão ii-V-I em Sol no piano roll").
2. Eu escolho a(s) ferramenta(s) MCP certa(s), com os parâmetros
   extraídos do pedido.
3. A ferramenta chama `reaper_bridge`, que executa via `reapy` — a
   mudança acontece ao vivo, na tela do REAPER.
4. Eu confirmo o que foi feito (ou repito o erro de forma clara, se
   algo falhou).

## Tratamento de erros

- REAPER fechado ou `reapy` não configurado → `ReaperBridgeError` com
  mensagem "REAPER não está aberto ou não foi configurado corretamente,
  abra o REAPER e tente de novo".
- Faixa/FX inexistente → erro citando o nome pedido e as opções
  disponíveis no projeto atual.
- Falha de renderização → repassa a mensagem de erro do próprio REAPER
  quando disponível.
- Nenhuma chamada MCP deixa uma exceção crua chegar até o Claude Code —
  tudo vira uma mensagem de erro estruturada.

## Testes

- `reaper_bridge`: testes unitários mockando `reapy` (mesmo padrão já
  usado em `music_studio` para mockar `ace_step_client`) — verificam
  que as chamadas certas do `reapy` são feitas e que os erros são
  traduzidos corretamente.
- `midi.py` (geração/análise com `music21`): testes reais, sem precisar
  do REAPER — validam que uma progressão pedida gera as notas certas, e
  que uma sequência de notas conhecida é analisada corretamente.
- `mcp_server.py`: testes de despacho de ferramenta com `reaper_bridge`
  mockado.
- Integração de ponta a ponta (com o REAPER de verdade aberto): não dá
  para automatizar em CI. Fica como checklist manual no `README.md` do
  projeto — mesma postura já adotada para o frontend do `music-studio`.

## Pré-requisitos (já concluídos nesta máquina)

1. REAPER instalado e abrindo sem erros.
2. Python habilitado no ReaScript (Preferences → Plug-ins → ReaScript),
   apontando para o Python do `uv`
   (`C:\Users\Celso\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none`).
3. `python-reapy` instalado no `.venv` de `C:\estudos\daw_music_studio`
   (`uv add python-reapy`).
4. `reapy.configure_reaper()` rodado com o REAPER aberto, registro de
   ação corrigido em `reaper-kb.ini` (havia uma entrada antiga de um
   projeto anterior apontando para um caminho inexistente — corrigida).
5. Conexão verificada: `uv run python -c "import reapy;
   print(reapy.Project())"` retorna o projeto ativo sem erro.

Dependências que ainda faltam instalar (parte da implementação, não
pré-requisito manual): `mcp` (SDK do servidor MCP) e `music21`.

## Próximos specs (fora do escopo deste documento)

- Reaproveitar `reaper_bridge` atrás de um chat na web app do
  `music-studio`, se/quando fizer falta.
- Presets de mixagem/masterização mais sofisticados (side-chain,
  multibanda), se o preset padrão não for suficiente na prática.
