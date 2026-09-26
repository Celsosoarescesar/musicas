from __future__ import annotations

from .errors import ReaperBridgeError
from .project import find_track

MIN_DB = -150.0
MAX_DB = 12.0


def _db_to_linear(db: float) -> float:
    return 10 ** (db / 20)


def set_volume(project, track_name: str, db: float):
    if not MIN_DB <= db <= MAX_DB:
        raise ReaperBridgeError(
            f"volume deve estar entre {MIN_DB} e {MAX_DB} dB, recebido: {db}"
        )
    track = find_track(project, track_name)
    try:
        track.volume = _db_to_linear(db)
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível definir o volume da faixa: verifique se o REAPER está aberto"
        ) from exc
    return track


def set_pan(project, track_name: str, pan: float):
    if not -1.0 <= pan <= 1.0:
        raise ReaperBridgeError(f"pan deve estar entre -1.0 e 1.0, recebido: {pan}")
    track = find_track(project, track_name)
    try:
        track.pan = pan
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível definir o pan da faixa: verifique se o REAPER está aberto"
        ) from exc
    return track


def set_mute(project, track_name: str, muted: bool):
    track = find_track(project, track_name)
    try:
        track.is_muted = muted
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível definir o mute da faixa: verifique se o REAPER está aberto"
        ) from exc
    return track


def set_solo(project, track_name: str, solo: bool):
    track = find_track(project, track_name)
    try:
        track.is_solo = solo
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível definir o solo da faixa: verifique se o REAPER está aberto"
        ) from exc
    return track
