from __future__ import annotations

import threading

from mcp.server import MCPServer

from reaper_bridge import mastering, midi, mixing
from reaper_bridge import project as project_ops
from reaper_bridge.connection import get_project
from reaper_bridge.errors import ReaperBridgeError

mcp = MCPServer("reaper-copilot")

# O MCPServer executa as tools em threads de trabalho, mas todas conversam com o
# REAPER pela mesma conexão reapy (sem lock próprio). Serializamos as chamadas
# para que requisições/respostas concorrentes não se misturem.
_REAPER_LOCK = threading.Lock()


def _run(operation):
    with _REAPER_LOCK:
        try:
            return operation()
        except ReaperBridgeError as exc:
            return f"Erro: {exc}"
        except Exception as exc:
            return f"Erro inesperado: {exc}"


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
        try:
            resolved_name = track.name
        except Exception as exc:
            raise ReaperBridgeError(
                f"áudio importado, mas não foi possível confirmar o nome da faixa: {exc}"
            ) from exc
        return f"Áudio importado na faixa '{resolved_name}'."
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
        try:
            names = [fx.name for fx in fxs]
        except Exception as exc:
            raise ReaperBridgeError(
                f"master aplicado, mas não foi possível confirmar os plugins: {exc}"
            ) from exc
        return "Master aplicado: " + ", ".join(names)
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
