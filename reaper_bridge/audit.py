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


def find_bypassed_fx(project) -> list[tuple[str, str]]:
    try:
        pairs: list[tuple[str, str]] = []
        for track in project.tracks:
            for fx in track.fxs:
                if not fx.is_enabled:
                    pairs.append((track.name, fx.name))
        return pairs
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar plugins bypassed: verifique se o REAPER está aberto"
        ) from exc


def find_multi_destination_sends(project) -> list[tuple[str, list[str]]]:
    try:
        result: list[tuple[str, list[str]]] = []
        for track in project.tracks:
            if track.n_sends > 1:
                destinations = [send.dest_track.name for send in track.sends]
                result.append((track.name, destinations))
        return result
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar o roteamento das faixas: verifique se o REAPER está aberto"
        ) from exc
