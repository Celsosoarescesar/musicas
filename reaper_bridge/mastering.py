from __future__ import annotations

import os
import time

import reapy

from .errors import ReaperBridgeError

MASTER_CHAIN_PLUGINS = ["ReaEQ (Cockos)", "ReaComp (Cockos)", "ReaLimit (Cockos)"]


def apply_master_chain(project):
    try:
        master = project.master_track
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível acessar a faixa mestre: verifique se o REAPER está aberto"
        ) from exc
    added = []
    for plugin_name in MASTER_CHAIN_PLUGINS:
        try:
            fx = master.add_fx(plugin_name)
        except ValueError as exc:
            raise ReaperBridgeError(
                f"plugin de master '{plugin_name}' não encontrado no REAPER"
            ) from exc
        except Exception as exc:
            raise ReaperBridgeError(
                f"não foi possível adicionar o plugin '{plugin_name}' à faixa mestre: "
                "verifique se o REAPER está aberto"
            ) from exc
        added.append(fx)
    return added


# Command ID da ação nativa "File: Render project, using the most recent render
# settings, auto-close render dialog". Confirmado ao vivo contra um REAPER real
# via `reapy.reascript_api.kbd_getTextFromCmd(42230, 0)`, que devolveu exatamente
# o nome desta ação. Se o REAPER mudar esse ID em uma versão futura, reconferir
# da mesma forma antes de confiar nele em produção.
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
    previous_mtime = (
        os.path.getmtime(output_path) if os.path.isfile(output_path) else None
    )
    try:
        project.set_info_string("RENDER_FILE", directory)
        project.set_info_string("RENDER_PATTERN", name)
        reapy.reascript_api.Main_OnCommand(RENDER_ACTION_ID, 0)
    except Exception as exc:
        raise ReaperBridgeError(f"falha ao iniciar o render: {exc}") from exc

    def _render_is_done() -> bool:
        # Se o arquivo já existia (re-render no mesmo caminho), só consideramos
        # concluído quando a data de modificação avançar.
        if not os.path.isfile(output_path):
            return False
        if previous_mtime is None:
            return True
        return os.path.getmtime(output_path) > previous_mtime

    deadline = time.monotonic() + timeout_seconds
    while not _render_is_done():
        if time.monotonic() > deadline:
            raise ReaperBridgeError(
                f"o render não terminou em {timeout_seconds:.0f}s, verifique manualmente "
                f"se o arquivo foi criado em {output_path}"
            )
        time.sleep(0.5)
    return output_path
