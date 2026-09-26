from __future__ import annotations

import os
import subprocess

from .errors import ReaperBridgeError
from .project import find_track, import_audio

PYTHON_CANDIDATES = ["python", "py -3", "python3"]
DEFAULT_MODEL = "htdemucs_6s"
DEFAULT_TIMEOUT_SECONDS = 1200.0
_STEM_FILE_EXTENSIONS = (".wav", ".mp3")


def find_python_command() -> str:
    """Acha um comando Python com o Demucs instalado.

    Não basta confirmar que o comando existe (ex.: `--version`) -- dentro do
    ambiente do uv, "python" existe e responde, mas é o Python deste projeto,
    que não tem o Demucs instalado. Por isso o probe importa `demucs` de
    verdade, para achar o Python certo (o do sistema, com o setup manual já
    feito), mesmo que ele apareça depois de outros "python" no PATH.
    """
    for candidate in PYTHON_CANDIDATES:
        try:
            result = subprocess.run(
                candidate.split() + ["-c", "import demucs"],
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return candidate
    raise ReaperBridgeError(
        "nenhum comando Python com o Demucs instalado foi encontrado no PATH "
        "do sistema (tentei: "
        + ", ".join(PYTHON_CANDIDATES)
        + "). Instale o Python, rode `pip install demucs soundfile==0.12.1` "
        "e adicione ao PATH."
    )


def split_stems(
    project,
    track_name: str,
    model: str = DEFAULT_MODEL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Separa os stems do audio de uma faixa usando Demucs (processo Python externo).

    Roda o Demucs como um subprocesso do nosso próprio processo -- o REAPER
    nunca fica bloqueado durante a separação, e nenhuma caixa de diálogo pode
    aparecer. Ao terminar, importa cada arquivo de stem gerado como uma nova
    faixa (via import_audio) e devolve os nomes das faixas criadas.
    """
    track = find_track(project, track_name)
    source_path = get_source_path(track)
    if not os.path.isfile(source_path):
        raise ReaperBridgeError(f"arquivo de origem não encontrado: {source_path}")

    python_cmd = find_python_command()

    song_name = os.path.splitext(os.path.basename(source_path))[0]
    output_dir = os.path.join(os.path.dirname(source_path), f"{song_name}_stems")

    command = python_cmd.split() + [
        "-m", "demucs.separate",
        "-n", model,
        "-o", output_dir,
        source_path,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReaperBridgeError(
            f"a separação de stems não terminou em {timeout_seconds:.0f}s"
        ) from exc

    if result.returncode != 0:
        tail = "\n".join((result.stderr or "").splitlines()[-10:])
        raise ReaperBridgeError(f"o Demucs falhou ao separar os stems: {tail}")

    stems_dir = os.path.join(output_dir, model, song_name)
    if not os.path.isdir(stems_dir):
        raise ReaperBridgeError(
            f"o Demucs terminou mas a pasta de stems não foi encontrada: {stems_dir}"
        )

    stem_files = sorted(
        f for f in os.listdir(stems_dir) if f.lower().endswith(_STEM_FILE_EXTENSIONS)
    )
    if not stem_files:
        raise ReaperBridgeError(f"nenhum stem foi gerado em {stems_dir}")

    created_tracks = []
    for filename in stem_files:
        stem_name = os.path.splitext(filename)[0]
        stem_path = os.path.join(stems_dir, filename)
        new_track_name = f"{track_name}_{stem_name}"
        import_audio(project, stem_path, track_name=new_track_name)
        created_tracks.append(new_track_name)
    return created_tracks


def get_source_path(track) -> str:
    """Retorna o caminho do arquivo de audio de origem do primeiro item da faixa."""
    if not track.items:
        raise ReaperBridgeError(f"faixa '{track.name}' não tem nenhum item de áudio")
    item = track.items[0]
    try:
        path = item.active_take.source.filename
    except Exception as exc:
        raise ReaperBridgeError(
            f"não foi possível ler o arquivo de origem da faixa '{track.name}': "
            "verifique se o REAPER está aberto"
        ) from exc
    if not path:
        raise ReaperBridgeError(
            f"a faixa '{track.name}' não tem um arquivo de áudio de origem válido"
        )
    return path
