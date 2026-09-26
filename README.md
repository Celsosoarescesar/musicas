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
- [ ] "Renomeia a faixa bateria para drums" → o nome da faixa muda no REAPER.
- [ ] "Importa esse áudio: `<caminho de um .wav de teste>`" → aparece uma nova faixa com
      o áudio, começando em 0:00.
- [ ] "Aumenta o volume da faixa drums para -3dB" e "muda o pan para a esquerda" →
      o fader e o pan se movem no REAPER.
- [ ] "Muta a faixa drums" → o ícone de mute acende no REAPER; "desmuta a faixa drums" →
      o ícone de mute apaga.
- [ ] "Faz solo na faixa drums" → apenas a faixa drums é audível; "tira o solo da faixa
      drums" → as outras faixas voltam a ser audíveis.
- [ ] "Adiciona um ReaEQ na faixa drums" → o plugin aparece na chain de FX da faixa.
- [ ] "Muda o parâmetro de frequência do ReaEQ para 500 Hz" → o valor do parâmetro muda
      no REAPER.
- [ ] "Aplica a chain de master" → ReaEQ, ReaComp e ReaLimit aparecem na faixa mestre.
- [ ] "Renderiza o projeto para `<pasta>\teste.wav`" → o arquivo aparece na pasta.
- [ ] "Gera uma escala de Dó maior no piano roll da faixa piano" → as notas aparecem no
      piano roll dessa faixa.
- [ ] "Gera um acorde de Dó maior no piano roll da faixa piano" → as notas do acorde
      aparecem no piano roll dessa faixa.
- [ ] "Gera uma progressão de acordes (Dó, Fá, Sol) no piano roll da faixa piano" →
      os acordes aparecem sequencialmente no piano roll dessa faixa.
- [ ] "Analisa o que eu toquei nessa faixa" (depois de tocar/gravar algo com um teclado
      MIDI conectado ao REAPER numa faixa MIDI) → devolve uma análise de
      tonalidade/acorde coerente com o que foi tocado.
