from __future__ import annotations

import os

import reapy

from .errors import ReaperBridgeError


def list_tracks(project: "reapy.Project") -> list[str]:
    try:
        return [track.name for track in project.tracks]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível listar as faixas: verifique se o REAPER está aberto"
        ) from exc


def find_track(project: "reapy.Project", name: str):
    try:
        matches = [track for track in project.tracks if track.name == name]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível buscar faixas: verifique se o REAPER está aberto"
        ) from exc

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
    try:
        return project.add_track(index=project.n_tracks, name=name)
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível criar a faixa: verifique se o REAPER está aberto"
        ) from exc


def rename_track(project: "reapy.Project", name: str, new_name: str):
    track = find_track(project, name)
    try:
        track.name = new_name
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível renomear a faixa: verifique se o REAPER está aberto"
        ) from exc
    return track


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
    try:
        project.cursor_position = 0.0
        reapy.reascript_api.InsertMedia(file_path, 1)  # mode 1 = adicionar em nova faixa
        track = project.tracks[project.n_tracks - 1]
        if track_name:
            track.name = track_name
    except Exception as exc:
        raise ReaperBridgeError(f"não foi possível importar o áudio: {exc}") from exc
    return track
