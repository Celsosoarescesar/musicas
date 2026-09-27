from __future__ import annotations

import reapy

from reaper_bridge.connection import get_project
from reaper_bridge.project import clear_track_items, get_or_create_track


def lesson_track(name: str) -> tuple["reapy.Project", "reapy.Track"]:
    """Conecta ao REAPER e garante uma faixa dedicada e limpa para a lição.

    Cria a faixa se não existir; se já existir (de uma execução anterior da
    mesma lição), limpa os itens MIDI antes de devolver, para que rodar a
    lição de novo não empilhe notas repetidas.
    """
    project = get_project()
    track = get_or_create_track(project, name)
    clear_track_items(track)
    return project, track
