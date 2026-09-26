"""Reverse-proxy + stem-separation server for the ace-step-api Kaggle kernel.

Runs as a second subprocess alongside acestep.api_server (see
ace_step_server.py in this same folder), on the port ngrok actually
tunnels. No heavy imports at module level (no torch, no demucs) --
fastapi/httpx/uvicorn are already this repo's own project dependencies
(used by the music-studio backend), so this whole file is testable
locally without a GPU or the `demucs` package installed. See
docs/superpowers/specs/2026-09-19-demucs-kernel-proxy-design.md.
"""

import json
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel


def parse_audio_path(file_ref: str) -> str:
    """Extract the raw filesystem path from a `/v1/audio?path=...`-style string.

    `file_ref` is the same opaque string `generate_music`'s result
    already returns in `result["file"]` -- a relative URL with the real
    path URL-encoded in its `path` query parameter.
    """
    parsed = urlparse(file_ref)
    query = parse_qs(parsed.query)
    try:
        path_values = query["path"]
    except KeyError as exc:
        raise ValueError(
            f"Nao foi possivel extrair o caminho de {file_ref!r} -- esperava um "
            "parametro de query 'path'"
        ) from exc
    return unquote(path_values[0])


def build_demucs_command(
    input_path: Path, out_dir: Path, *, model: str = "htdemucs_6s", device: str = "cuda"
) -> list[str]:
    """Build the `python -m demucs` command to separate `input_path` into `out_dir`."""
    return [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        model,
        "-d",
        device,
        "--out",
        str(out_dir),
        str(input_path),
    ]


# htdemucs_6s (not the 4-stem htdemucs) -- adds guitar and piano as their own
# stems. This is the practical ceiling among mature, widely-used open models;
# no reliable model separates individual instruments beyond this (confirmed
# via research 2026-09-26, see project memory).
_STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")


def stems_from_output_dir(out_dir: Path, model: str, track_name: str) -> dict[str, Path]:
    """Map Demucs' output directory layout to the 6 expected stem file paths.

    Demucs writes to
    `<out_dir>/<model>/<track_name>/{vocals,drums,bass,guitar,piano,other}.wav`.
    Raises ValueError (never a partial dict) if any expected stem is missing.
    """
    track_dir = Path(out_dir) / model / track_name
    stems = {name: track_dir / f"{name}.wav" for name in _STEM_NAMES}
    missing = [name for name, path in stems.items() if not path.exists()]
    if missing:
        found = sorted(p.name for p in track_dir.glob("*")) if track_dir.exists() else []
        raise ValueError(
            f"Demucs nao gerou os stems esperados em {track_dir} -- faltando: "
            f"{', '.join(missing)} (arquivos encontrados: {found})"
        )
    return stems


class SeparateTaskRequest(BaseModel):
    file: str


class SeparateTaskResponse(BaseModel):
    task_id: str


class QueryTaskListRequest(BaseModel):
    task_id_list: list[str]


def _check_api_key(authorization: str | None, api_key: str) -> None:
    if authorization != f"Bearer {api_key}":
        raise HTTPException(401, "Chave de API invalida ou ausente")


def create_app(acestep_base_url: str, api_key: str) -> FastAPI:
    app = FastAPI(title="ACE-Step proxy + stem separation")
    tasks: dict[str, dict] = {}
    tasks_lock = threading.Lock()

    def _run_separation(task_id: str, input_path: str) -> None:
        out_dir = Path(input_path).parent / "stems" / task_id
        out_dir.mkdir(parents=True, exist_ok=True)
        track_name = Path(input_path).stem
        command = build_demucs_command(Path(input_path), out_dir)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            stems = stems_from_output_dir(out_dir, "htdemucs_6s", track_name)
            result = {
                name: f"/v1/stems?path={quote(str(path), safe='')}"
                for name, path in stems.items()
            }
            with tasks_lock:
                tasks[task_id] = {"status": 1, "result": json.dumps(result)}
        except subprocess.CalledProcessError as exc:
            # Same "prefer stderr, fall back to str(exc)" pattern already
            # used by kagglelab.song_lyrics for a failed subprocess --
            # str(CalledProcessError) alone doesn't include stderr, and
            # stderr is exactly where Demucs would report e.g. a CUDA OOM.
            detail = (exc.stderr or "").strip() or str(exc)
            with tasks_lock:
                tasks[task_id] = {"status": 2, "result": detail}
        except Exception as exc:
            with tasks_lock:
                tasks[task_id] = {"status": 2, "result": str(exc)}

    @app.post("/separate_task", response_model=SeparateTaskResponse)
    def separate_task(
        payload: SeparateTaskRequest, authorization: str | None = Header(None)
    ) -> SeparateTaskResponse:
        _check_api_key(authorization, api_key)
        input_path = parse_audio_path(payload.file)
        task_id = str(uuid.uuid4())
        with tasks_lock:
            tasks[task_id] = {"status": 0, "result": None}
        thread = threading.Thread(
            target=_run_separation, args=(task_id, input_path), daemon=True
        )
        thread.start()
        return SeparateTaskResponse(task_id=task_id)

    @app.post("/query_separation_result")
    def query_separation_result(
        payload: QueryTaskListRequest, authorization: str | None = Header(None)
    ) -> list[dict]:
        _check_api_key(authorization, api_key)
        with tasks_lock:
            return [
                {"task_id": task_id, **tasks[task_id]}
                for task_id in payload.task_id_list
                if task_id in tasks
            ]

    @app.get("/v1/stems")
    def get_stem(path: str, authorization: str | None = Header(None)) -> FileResponse:
        _check_api_key(authorization, api_key)
        if not Path(path).exists():
            raise HTTPException(404, f"Arquivo nao encontrado: {path}")
        return FileResponse(path, media_type="audio/wav")

    @app.api_route("/{full_path:path}", methods=["GET", "POST"])
    async def proxy_passthrough(full_path: str, request: Request) -> Response:
        body = await request.body()
        forwarded_headers = {
            key: value for key, value in request.headers.items() if key.lower() != "host"
        }
        async with httpx.AsyncClient() as upstream:
            upstream_response = await upstream.request(
                request.method,
                f"{acestep_base_url}/{full_path}",
                params=request.query_params,
                headers=forwarded_headers,
                content=body,
                timeout=60.0,
            )
        response_headers = {
            key: value
            for key, value in upstream_response.headers.items()
            if key.lower() not in ("content-length", "transfer-encoding")
        }
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=response_headers,
        )

    return app


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        create_app(os.environ["ACESTEP_INTERNAL_URL"], os.environ["ACE_STEP_API_KEY"]),
        host="0.0.0.0",
        port=int(os.environ.get("PROXY_PORT", "8188")),
    )
