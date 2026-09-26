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


def _find_fx(track, fx_name: str):
    try:
        # Lê os nomes aqui dentro também: no reapy cada fx.name é uma chamada remota.
        fxs = [(fx, fx.name) for fx in track.fxs]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível listar os plugins da faixa: verifique se o REAPER está aberto"
        ) from exc
    for fx, name in fxs:
        if name == fx_name:
            return fx
    available = ", ".join(name for _, name in fxs) or "(nenhum)"
    raise ReaperBridgeError(
        f"plugin '{fx_name}' não está na faixa, plugins presentes: {available}"
    )


def add_fx(project, track_name: str, fx_name: str):
    track = find_track(project, track_name)
    try:
        return track.add_fx(fx_name)
    except ValueError as exc:
        raise ReaperBridgeError(f"plugin '{fx_name}' não encontrado no REAPER") from exc
    except Exception as exc:
        raise ReaperBridgeError(
            f"não foi possível adicionar o plugin '{fx_name}' à faixa '{track_name}': "
            "verifique se o REAPER está aberto"
        ) from exc


def set_fx_param(project, track_name: str, fx_name: str, param_name: str, value: float):
    if not 0.0 <= value <= 1.0:
        raise ReaperBridgeError(
            f"valor de parâmetro deve estar entre 0.0 e 1.0 (normalizado), recebido: {value}"
        )
    track = find_track(project, track_name)
    fx = _find_fx(track, fx_name)
    try:
        # Idem: cada p.name é uma chamada remota ao REAPER.
        params = [(p, p.name) for p in fx.params]
    except Exception as exc:
        raise ReaperBridgeError(
            f"não foi possível listar os parâmetros de '{fx_name}': verifique se o REAPER está aberto"
        ) from exc
    param = next((p for p, name in params if name == param_name), None)
    if param is None:
        available = ", ".join(name for _, name in params) or "(nenhum)"
        raise ReaperBridgeError(
            f"parâmetro '{param_name}' não existe em '{fx_name}', parâmetros "
            f"disponíveis: {available}"
        )
    try:
        param.normalized = value
    except Exception as exc:
        raise ReaperBridgeError(
            f"não foi possível definir o parâmetro '{param_name}': verifique se o REAPER está aberto"
        ) from exc
    return param
