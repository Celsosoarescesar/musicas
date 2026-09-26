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
