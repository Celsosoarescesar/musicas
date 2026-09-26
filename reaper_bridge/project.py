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
