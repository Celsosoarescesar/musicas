from __future__ import annotations

import os

from .errors import ReaperBridgeError
from .project import create_track, import_audio, list_tracks

STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")
GUIDE_TRACK_NAME = "guia_ia"
VOICE_TRACK_NAME = "voz_caelum"


def _track_name_for(stem_name: str) -> str:
    return GUIDE_TRACK_NAME if stem_name == "vocals" else stem_name


def build_vocal_session(project, stems_dir: str, song_id: int) -> list[str]:
    """Monta a sessao de gravacao de uma faixa do album.

    Importa os stems `<song_id>_stem_<nome>.wav` de `stems_dir` como faixas
    (o stem `vocals` vira `guia_ia`, silenciado: so referencia de pronuncia e
    fraseado) e cria a faixa `voz_caelum`, armada para gravar. Se nao houver o
    stem `vocals` (base instrumental), nao cria `guia_ia`. Devolve os nomes das
    faixas criadas, na ordem de criacao.

    Falha ANTES de qualquer mudanca no projeto se a pasta nao existe, nao ha
    nenhum stem dessa musica, ou se alguma faixa-alvo ja existe no projeto
    (rodar duas vezes nao duplica nada nem toca em faixas do usuario).
    Escolher a entrada de audio da faixa `voz_caelum` e manual no REAPER.
    """
    if not os.path.isdir(stems_dir):
        raise ReaperBridgeError(f"pasta de stems não encontrada: {stems_dir}")

    stems = []
    for stem_name in STEM_NAMES:
        path = os.path.join(stems_dir, f"{song_id}_stem_{stem_name}.wav")
        if os.path.isfile(path):
            stems.append((stem_name, path))
    if not stems:
        raise ReaperBridgeError(
            f"nenhum stem da música {song_id} encontrado em {stems_dir} "
            f"(esperado: {song_id}_stem_<nome>.wav)"
        )

    # Guia fica por ultimo entre os stems: so a ordem de criacao das faixas muda.
    stems.sort(key=lambda item: item[0] == "vocals")
    target_names = [_track_name_for(name) for name, _ in stems] + [VOICE_TRACK_NAME]
    existing = set(list_tracks(project))
    clashes = [name for name in target_names if name in existing]
    if clashes:
        raise ReaperBridgeError(
            f"já existe(m) no projeto faixa(s) com o nome: {', '.join(clashes)} "
            "-- use um projeto novo e vazio para montar a sessão"
        )

    created = []
    for stem_name, path in stems:
        track_name = _track_name_for(stem_name)
        track = import_audio(project, path, track_name=track_name)
        if stem_name == "vocals":
            try:
                track.is_muted = True
            except Exception as exc:
                raise ReaperBridgeError(
                    "não foi possível silenciar a faixa guia_ia: verifique se o REAPER está aberto"
                ) from exc
        created.append(track_name)

    voice = create_track(project, VOICE_TRACK_NAME)
    try:
        voice.set_info_value("I_RECARM", 1)
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível armar a faixa voz_caelum para gravação: "
            "verifique se o REAPER está aberto"
        ) from exc
    created.append(VOICE_TRACK_NAME)
    return created
