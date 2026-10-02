from __future__ import annotations

from .errors import ReaperBridgeError


def find_armed_tracks(project) -> list[str]:
    try:
        return [
            track.name
            for track in project.tracks
            if track.get_info_value("I_RECARM") == 1.0
        ]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar faixas armadas: verifique se o REAPER está aberto"
        ) from exc


def find_muted_tracks(project) -> list[str]:
    try:
        return [track.name for track in project.tracks if track.is_muted]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar faixas mutadas: verifique se o REAPER está aberto"
        ) from exc


def find_empty_tracks(project) -> list[str]:
    try:
        return [track.name for track in project.tracks if track.n_items == 0]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar faixas vazias: verifique se o REAPER está aberto"
        ) from exc
