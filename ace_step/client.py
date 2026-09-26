"""HTTP client for the ACE-Step 1.5 API (native `acestep` package REST server).

Ver docs/superpowers/specs/2026-09-19-ace-step-native-package-design.md (a
API que este cliente chama) e
docs/superpowers/specs/2026-09-13-ace-step-orchestrator-design.md (este
orquestrador, Fase 2).
"""

import json
import time
from pathlib import Path

import requests


class AceStepApiError(Exception):
    """Raised when a call to the ACE-Step API fails."""


def check_health(base_url: str, timeout: float = 10.0) -> dict:
    """Call GET /health. Raises AceStepApiError if unreachable, non-200, or

    if the reported `status` isn't "ok" (e.g. "loading" -- server process is
    up but the model isn't ready yet).
    """
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
    except requests.RequestException as exc:
        raise AceStepApiError(
            f"Nao foi possivel conectar em {base_url}/health -- confira se o "
            "kernel esta 'running' (uv run scripts/kernel_status.py "
            f"celsosoarescesar/ace-step-api): {exc}"
        ) from exc
    if response.status_code != 200:
        raise AceStepApiError(
            f"GET /health devolveu {response.status_code}: {response.text[:200]}"
        )
    data = response.json()["data"]
    if data.get("status") != "ok":
        raise AceStepApiError(
            f"GET /health respondeu mas status nao e 'ok' (status atual: "
            f"{data.get('status')!r}) -- servidor pode estar de pe mas o "
            "modelo ainda nao terminou de carregar"
        )
    return data


def _post(base_url: str, path: str, api_key: str, payload: dict, timeout: float) -> dict:
    try:
        response = requests.post(
            f"{base_url}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise AceStepApiError(f"Falha ao chamar POST {path}: {exc}") from exc
    if response.status_code == 401:
        raise AceStepApiError(f"POST {path} devolveu 401 -- confira ACE_STEP_API_KEY no .env")
    if response.status_code != 200:
        raise AceStepApiError(
            f"POST {path} devolveu {response.status_code}: {response.text[:200]}"
        )
    body = response.json()
    if body.get("error"):
        raise AceStepApiError(f"POST {path} devolveu erro: {body['error']}")
    return body["data"]


def _post_raw(base_url: str, path: str, api_key: str, payload: dict, timeout: float):
    """Like _post, but for proxy_server.py's own endpoints (/separate_task,
    /query_separation_result), which return their JSON body directly --
    confirmed live, unlike acestep's own endpoints (proxied through
    unchanged), these are NOT wrapped in a {"data": ..., "error": ...}
    envelope. Using _post here crashed with KeyError('data') against the
    real server.
    """
    try:
        response = requests.post(
            f"{base_url}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise AceStepApiError(f"Falha ao chamar POST {path}: {exc}") from exc
    if response.status_code == 401:
        raise AceStepApiError(f"POST {path} devolveu 401 -- confira ACE_STEP_API_KEY no .env")
    if response.status_code != 200:
        raise AceStepApiError(
            f"POST {path} devolveu {response.status_code}: {response.text[:200]}"
        )
    return response.json()


# How many consecutive /query_result poll failures (connection errors, non-200,
# etc.) to tolerate before giving up -- a single transient failure shouldn't
# abort a generation that's still succeeding server-side and losing the
# task_id with it.
_MAX_CONSECUTIVE_POLL_FAILURES = 3


def generate_music(
    base_url: str,
    api_key: str,
    *,
    prompt: str,
    lyrics: str,
    duration: float,
    seed: int,
    bpm: int | None,
    keyscale: str | None,
    vocal_language: str,
    timeout: float = 300.0,
    poll_interval: float = 5.0,
) -> dict:
    """Submit a text2music task and poll until it finishes.

    Returns the parsed first item of the task's `result` list (a dict with
    at least a `"file"` key -- a relative `/v1/audio?path=...` URL, ready to
    pass straight to `download_audio`).
    """
    release_payload = {
        "prompt": prompt,
        "lyrics": lyrics,
        "audio_duration": duration,
        # audio_format defaults to "mp3" server-side; keep "wav" so
        # song_mastering.normalize_loudness (soundfile/libsndfile) doesn't
        # need MP3 decode support.
        "audio_format": "wav",
        "use_random_seed": False,
        "seed": seed,
        "bpm": bpm,
        "key_scale": keyscale,
        "vocal_language": vocal_language,
        "task_type": "text2music",
    }
    task = _post(base_url, "/release_task", api_key, release_payload, timeout=30.0)
    try:
        task_id = task["task_id"]
    except KeyError as exc:
        raise AceStepApiError(
            f"POST /release_task nao devolveu 'task_id' na resposta -- esperava "
            f"um dict com essa chave, recebi: {task!r}"
        ) from exc

    deadline = time.monotonic() + timeout
    consecutive_poll_failures = 0
    while True:
        try:
            query = _post(
                base_url, "/query_result", api_key, {"task_id_list": [task_id]}, timeout=30.0
            )
        except AceStepApiError as exc:
            consecutive_poll_failures += 1
            if consecutive_poll_failures > _MAX_CONSECUTIVE_POLL_FAILURES:
                raise AceStepApiError(
                    f"POST /query_result falhou {consecutive_poll_failures} vezes "
                    f"seguidas para a task {task_id} -- desistindo, mas a geracao "
                    "pode continuar rodando no servidor; consulte /query_result "
                    f"manualmente com task_id={task_id!r} mais tarde para tentar "
                    f"recuperar o arquivo. Ultimo erro: {exc}"
                ) from exc
            time.sleep(poll_interval)
            continue
        consecutive_poll_failures = 0

        if not query:
            raise AceStepApiError(
                f"POST /query_result devolveu lista vazia para a task {task_id} -- "
                "a task pode ter sido purgada do servidor ou o servidor "
                f"reiniciou; task_id={task_id!r} para tentar consultar manualmente"
            )
        entry = query[0]
        try:
            status = entry["status"]
        except KeyError as exc:
            raise AceStepApiError(
                f"Resposta de /query_result para a task {task_id} nao tem campo "
                f"'status' -- esperava um dict com essa chave, recebi: {entry!r}"
            ) from exc
        if status == 1:
            return json.loads(entry["result"])[0]
        if status == 2:
            raise AceStepApiError(f"Geracao falhou (task {task_id}): {entry.get('result')}")
        if time.monotonic() >= deadline:
            raise AceStepApiError(
                f"Timeout de {timeout}s esperando a task {task_id} terminar -- ela "
                "pode continuar rodando no servidor; consulte /query_result "
                f"manualmente com task_id={task_id!r} mais tarde para tentar "
                "recuperar o arquivo"
            )
        time.sleep(poll_interval)


def separate_stems(
    base_url: str,
    api_key: str,
    file_path: str,
    *,
    timeout: float = 300.0,
    poll_interval: float = 5.0,
) -> dict:
    """Submit a stem-separation task and poll until it finishes.

    `file_path` is the same opaque `/v1/audio?path=...`-style string
    `generate_music`'s result already returns in `result["file"]`.
    Returns a dict of 4 stem names ("vocals", "drums", "bass", "other")
    to `/v1/stems?path=...`-style strings, ready to pass straight to
    `download_audio` (same as generation's output already is).
    """
    task = _post_raw(base_url, "/separate_task", api_key, {"file": file_path}, timeout=30.0)
    try:
        task_id = task["task_id"]
    except KeyError as exc:
        raise AceStepApiError(
            f"POST /separate_task nao devolveu 'task_id' na resposta -- esperava "
            f"um dict com essa chave, recebi: {task!r}"
        ) from exc

    deadline = time.monotonic() + timeout
    while True:
        query = _post_raw(
            base_url, "/query_separation_result", api_key, {"task_id_list": [task_id]}, timeout=30.0
        )
        if not query:
            raise AceStepApiError(
                f"POST /query_separation_result devolveu lista vazia para a task "
                f"{task_id} -- a task pode ter sido purgada do servidor; "
                f"task_id={task_id!r} para tentar consultar manualmente"
            )
        entry = query[0]
        status = entry["status"]
        if status == 1:
            return json.loads(entry["result"])
        if status == 2:
            raise AceStepApiError(f"Separacao de faixas falhou (task {task_id}): {entry.get('result')}")
        if time.monotonic() >= deadline:
            raise AceStepApiError(
                f"Timeout de {timeout}s esperando a separacao da task {task_id} "
                "terminar -- ela pode continuar rodando no servidor; consulte "
                "/query_separation_result manualmente com task_id="
                f"{task_id!r} mais tarde"
            )
        time.sleep(poll_interval)


def download_audio(
    base_url: str, api_key: str, file_path: str, dest_path: Path, timeout: float = 60.0
) -> Path:
    """Download generated audio from the server's /v1/audio URL. Returns dest_path."""
    try:
        response = requests.get(
            f"{base_url}{file_path}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise AceStepApiError(f"Falha ao baixar audio de {file_path}: {exc}") from exc
    if response.status_code != 200:
        raise AceStepApiError(
            f"GET {file_path} devolveu {response.status_code}: {response.text[:200]}"
        )
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(response.content)
    return dest_path
