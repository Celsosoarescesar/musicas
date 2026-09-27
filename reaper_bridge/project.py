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


def get_or_create_track(project: "reapy.Project", name: str):
    try:
        matches = [track for track in project.tracks if track.name == name]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível buscar faixas: verifique se o REAPER está aberto"
        ) from exc
    if len(matches) > 1:
        raise ReaperBridgeError(
            f"existe mais de uma faixa chamada '{name}' ({len(matches)} faixas), "
            "renomeie as faixas duplicadas antes de continuar"
        )
    if matches:
        return matches[0]
    return create_track(project, name)


def clear_track_items(track) -> None:
    try:
        for item in list(track.items):
            item.delete()
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível limpar os itens da faixa: verifique se o REAPER está aberto"
        ) from exc


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
    resolved_name = track_name or os.path.splitext(os.path.basename(file_path))[0]
    try:
        # Cria a faixa explicitamente e a seleciona como unica faixa selecionada,
        # em vez de deixar o InsertMedia decidir onde criar a faixa nova (modo 1):
        # com varias faixas ja no projeto, a faixa nova nem sempre fica no final
        # da lista, entao pegar project.tracks[-1] depois pode pegar a faixa
        # errada. Modo 0 = inserir o audio na faixa atualmente selecionada.
        track = project.add_track(index=project.n_tracks, name=resolved_name)
        track.make_only_selected_track()
        project.cursor_position = 0.0
        reapy.reascript_api.InsertMedia(file_path, 0)
    except Exception as exc:
        raise ReaperBridgeError(f"não foi possível importar o áudio: {exc}") from exc
    return track
