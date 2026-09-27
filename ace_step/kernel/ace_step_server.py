"""ACE-Step 1.5 music generation API — runs as a Kaggle kernel (GPU).

Roda dentro de um Kaggle Kernel, nao localmente (sem GPU local). Ver
docs/superpowers/specs/2026-09-19-ace-step-native-package-design.md para o
desenho completo (por que este script clona e roda o pacote `acestep`
nativo em vez de carregar o modelo direto via `diffusers`) e
docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md para o
desenho batch (por que nao ha mais servidor+tunel ngrok).

Este kernel roda uma unica musica por execucao: gera via `acestep.api_server`
(subido so em 127.0.0.1, nunca exposto), separa em stems via Demucs, escreve
tudo em /kaggle/working/output/ e termina -- sem servidor de longa duracao,
sem ngrok.

As funcoes abaixo (antes de main()) nao tem nenhum import de terceiros de
proposito: elas sao a unica parte deste arquivo testavel localmente (sem
GPU, sem o pacote `acestep`/demucs instalados). Tudo que precisa dessas
bibliotecas pesadas fica dentro de main(), com os imports feitos la dentro
(lazy) -- assim, importar este arquivo (via importlib, nos testes) nao
executa o git clone/pip install nem exige essas libs localmente.
"""

import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


_ACESTEP_REPO_URL = "https://github.com/ace-step/ACE-Step-1.5.git"
# Pinned (not tracking `main`) for reproducibility: the dtype patch and the
# flash-attn requirements.txt filter below are both matched against this
# exact commit's file contents (confirmed live -- an upstream reword of
# either file would silently break the string match). To pick up a future
# upstream fix, re-run `git ls-remote https://github.com/ace-step/ACE-Step-1.5.git HEAD`
# and update this constant (and re-verify the patches still match).
_ACESTEP_REPO_COMMIT = "ca1e85fe9430179831e6bc6be790c332190a3866"
# Not the XL (4B) turbo variant: confirmed live, `acestep-v15-xl-turbo` is
# a separate, additional download beyond the package's "core" bundle
# (INSTALL.md: "~10GB for core models", the main `Ace-Step1.5` download
# already includes the plain, non-XL `acestep-v15-turbo`) and its checkpoint
# alone filled the rest of /kaggle/working's disk mid-download
# (`OSError: [Errno 28] No space left on device`), even after --no-cache-dir
# freed up what pip's wheel cache was using. The non-XL turbo model is the
# package's own default (see `/v1/models`'s `is_default: true` in
# docs/en/API.md) and fits the disk budget the core download already
# accounts for.
_ACESTEP_MODEL_CONFIG = "acestep-v15-turbo"
_SECRETS_DATASET_REF = "celsosoarescesar/ace-step-api-secrets"
# acestep.api_server binds only to 127.0.0.1:_ACESTEP_PORT -- this kernel is
# the only client, there's no public HTTP endpoint anywhere anymore. See
# docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
_ACESTEP_PORT = 8189
# The native `acestep` package (github.com/ace-step/ACE-Step-1.5) replaces
# the diffusers-based server this file used to run directly. Confirmed live
# this session: diffusers' AceStepTransformer1DModel forward pass isn't
# multi-GPU-safe (accelerate's device_map sharding produced "tensors on two
# devices" errors -- an architecture-level incompatibility, not a config
# problem), so splitting the model across the kernel's 2 T4s was a dead
# end. The acestep package's own GPU_COMPATIBILITY.md documents up to
# 8-10 minutes of audio on a single 16-20GB GPU (a T4) via its own
# automatic INT8 quantization + CPU offload -- no multi-GPU needed for a
# 4-minute (240s) song.


def resolve_secrets_dataset_dir(kaggle_input_dir: Path, dataset_ref: str) -> Path:
    """Return whichever known Kaggle input-mount layout actually holds the secrets dataset.

    `dataset_ref` is the `owner/slug` string from kernel-metadata.json's
    `dataset_sources`. Kaggle has mounted a kernel's `dataset_sources` at
    `input/<slug>` (the documented, typical layout) but a nested
    `input/datasets/<owner>/<slug>` has also been observed live for this same
    dataset -- try the flat layout first, fall back to the nested one, and
    fall through to the flat path (letting `load_secrets` raise its own clear
    error) if neither actually has a `secrets.json`.
    """
    owner, _, slug = dataset_ref.partition("/")
    flat = Path(kaggle_input_dir) / slug
    if (flat / "secrets.json").exists():
        return flat
    nested = Path(kaggle_input_dir) / "datasets" / owner / slug
    if (nested / "secrets.json").exists():
        return nested
    return flat


def load_secrets(dataset_dir: Path) -> dict:
    """Load the kernel's secrets from a `secrets.json` file in a mounted Kaggle dataset.

    Works around a known Kaggle platform limitation, confirmed live: secrets
    attached through the web UI's Secrets panel do not carry over to kernels
    pushed via the API (`kaggle kernels push`) -- `kaggle_secrets.
    UserSecretsClient().get_secret(...)` fails with a ConnectionError in that
    case, even when the secret shows as attached in the UI. The workaround
    (Kaggle's own recommended pattern for this exact problem) is to store
    secrets in a private dataset instead and read them from its mounted path.
    """
    secrets_path = Path(dataset_dir) / "secrets.json"
    try:
        with open(secrets_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Dataset de secrets nao encontrado em {secrets_path} -- confira "
            "'dataset_sources' em kernel-metadata.json"
        ) from exc


def validate_secrets(secrets: dict, required_keys: list[str]) -> None:
    """Raise ValueError if any of `required_keys` is missing or empty in `secrets`."""
    missing = [key for key in required_keys if not secrets.get(key)]
    if missing:
        raise ValueError(
            f"Secrets ausentes ou vazios no dataset de secrets: {', '.join(missing)}"
        )


# Set by ace_step.kernel_render.render_job_kernel before this file is pushed
# to Kaggle -- see docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
# Left as None here so this file stays importable/testable on its own.
_JOB_B64: str | None = None

_STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")


def decode_job(job_b64: str) -> dict:
    """Decode the base64-JSON job embedded by render_job_kernel."""
    return json.loads(base64.b64decode(job_b64.encode("ascii")).decode("utf-8"))


def write_result_json(
    dest_path: Path,
    *,
    generation_status: str,
    generation_error: str | None,
    stems_status: str,
    stems_error: str | None,
) -> Path:
    """Write the kernel's result summary as JSON to dest_path. Returns dest_path."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(
        json.dumps(
            {
                "generation_status": generation_status,
                "generation_error": generation_error,
                "stems_status": stems_status,
                "stems_error": stems_error,
            }
        ),
        encoding="utf-8",
    )
    return dest_path


def parse_audio_path(file_ref: str) -> str:
    """Extract the raw filesystem path from a `/v1/audio?path=...`-style string.

    `file_ref` is the same opaque string the embedded acestep API's
    `/release_task` + `/query_result` result returns in its `file` field --
    a relative URL with the real path URL-encoded in its `path` query
    parameter.
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


def _post_json(url: str, payload: dict, *, headers: dict, timeout: float) -> dict:
    """POST JSON to url, return the parsed JSON response body."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method="POST", headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str, *, headers: dict, timeout: float) -> dict:
    """GET url, return the parsed JSON response body."""
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_health(base_url: str, api_key: str, *, timeout: float, poll_interval: float) -> None:
    """Poll base_url/health until it reports status 'ok'. Raises TimeoutError otherwise."""
    deadline = time.monotonic() + timeout
    headers = {"Authorization": f"Bearer {api_key}"}
    last_error = None
    while time.monotonic() < deadline:
        try:
            body = _get_json(f"{base_url}/health", headers=headers, timeout=10.0)
            status = body.get("data", {}).get("status")
            if status == "ok":
                return
            last_error = f"status atual: {status!r}"
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Timeout de {timeout}s esperando {base_url}/health responder 'ok' -- "
        f"ultimo erro: {last_error}"
    )


def wait_for_generation(
    base_url: str, api_key: str, job: dict, *, timeout: float, poll_interval: float
) -> str:
    """Submit `job` to /release_task and poll /query_result until done.

    Returns the raw `/v1/audio?path=...`-style file reference string on
    success. Raises RuntimeError if the task fails (or if acestep's own
    `{"data": ..., "error": ...}` envelope carries a truthy "error"),
    TimeoutError if it doesn't finish within `timeout` seconds.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "prompt": job["prompt"],
        "lyrics": job["lyrics"],
        "audio_duration": job["duration"],
        "audio_format": "wav",
        "use_random_seed": False,
        "seed": job["seed"],
        "bpm": job["bpm"],
        "key_scale": job["keyscale"],
        "vocal_language": job["vocal_language"],
        "task_type": "text2music",
    }
    task_envelope = _post_json(f"{base_url}/release_task", payload, headers=headers, timeout=30.0)
    if task_envelope.get("error"):
        raise RuntimeError(f"POST /release_task devolveu erro: {task_envelope['error']}")
    task_id = task_envelope["data"]["task_id"]

    deadline = time.monotonic() + timeout
    last_error = None
    while True:
        try:
            query_envelope = _post_json(
                f"{base_url}/query_result",
                {"task_id_list": [task_id]},
                headers=headers,
                timeout=30.0,
            )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
        else:
            if query_envelope.get("error"):
                raise RuntimeError(f"POST /query_result devolveu erro: {query_envelope['error']}")
            query = query_envelope["data"]
            if query:
                entry = query[0]
                status = entry["status"]
                if status == 1:
                    return json.loads(entry["result"])[0]["file"]
                if status == 2:
                    raise RuntimeError(f"Geracao falhou (task {task_id}): {entry.get('result')}")
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timeout de {timeout}s esperando a task {task_id} terminar -- "
                f"ultimo erro: {last_error}"
            )
        time.sleep(poll_interval)


def main():
    import logging
    import os
    import shutil
    import subprocess
    import time

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    secrets_dir = resolve_secrets_dataset_dir(Path("/kaggle/input"), _SECRETS_DATASET_REF)
    logger.info(f"Lendo secrets de: {secrets_dir}")
    secrets = load_secrets(secrets_dir)
    validate_secrets(secrets, ["ACE_STEP_API_KEY"])
    api_key = secrets["ACE_STEP_API_KEY"]

    def log_disk_usage(label: str) -> None:
        usage = shutil.disk_usage("/kaggle/working")
        logger.info(
            f"Disco em /kaggle/working ({label}): "
            f"{usage.free / 2**30:.1f}GiB livres de {usage.total / 2**30:.1f}GiB"
        )

    log_disk_usage("antes do clone")

    repo_dir = Path("/kaggle/working/ACE-Step-1.5")
    if not repo_dir.exists():
        logger.info(f"Clonando {_ACESTEP_REPO_URL} @ {_ACESTEP_REPO_COMMIT}...")
        # `git clone --depth 1` only shallow-clones a branch tip, not an
        # arbitrary SHA (not reliably supported across git versions) -- so
        # pin via init/remote/fetch-by-SHA/checkout instead, which still
        # only fetches the one pinned commit (shallow).
        subprocess.run(["git", "init", str(repo_dir)], check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", _ACESTEP_REPO_URL],
            cwd=str(repo_dir),
            check=True,
        )
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", _ACESTEP_REPO_COMMIT],
            cwd=str(repo_dir),
            check=True,
        )
        subprocess.run(
            ["git", "checkout", "-b", "main", "FETCH_HEAD"],
            cwd=str(repo_dir),
            check=True,
        )
    else:
        logger.info(f"{repo_dir} ja existe, pulando o clone.")
    log_disk_usage("depois do clone")

    # Confirmed live: the upstream acestep package sets self.dtype=float16
    # on pre-Ampere CUDA GPUs (T4/V100, compute capability < 8.0). float16
    # (5 exponent bits) can't represent this bf16-trained checkpoint's
    # activation range, and generation with non-empty lyrics deterministically
    # produces NaN/Inf latents partway through -- this is a known, currently
    # unfixed upstream bug (github.com/ace-step/ACE-Step-1.5/issues/1243,
    # closed "not planned"; the runtime's own suggested `ACESTEP_DTYPE=float32`
    # env var isn't wired to anything in this codebase, confirmed by reading
    # the source). A community fork (github.com/peter571/ACE-Step-1.5/tree/
    # fix-float32) fixes this by defaulting pre-Ampere CUDA to float32 instead
    # of float16 -- patch just that one line rather than pull in the whole
    # fork (which is 21 commits behind upstream).
    orchestrator_path = repo_dir / "acestep/core/generation/handler/init_service_orchestrator.py"
    orchestrator_src = orchestrator_path.read_text(encoding="utf-8")
    _old_dtype_block = (
        "                else:\n"
        "                    self.dtype = torch.float16\n"
        "                    logger.info(\n"
        '                        "[initialize_service] Pre-Ampere CUDA detected: "\n'
        '                        "using float16 instead of bfloat16."\n'
        "                    )\n"
    )
    _new_dtype_block = (
        "                else:\n"
        "                    self.dtype = torch.float32\n"
        "                    logger.info(\n"
        '                        "[initialize_service] Pre-Ampere CUDA detected: "\n'
        '                        "using float32 (not float16) -- avoids NaN/Inf in "\n'
        '                        "lyric conditioning, confirmed live -- see "\n'
        '                        "github.com/ace-step/ACE-Step-1.5/issues/1243."\n'
        "                    )\n"
    )
    if _new_dtype_block in orchestrator_src:
        logger.info("Patch de dtype (float32 em pre-Ampere) ja aplicado, pulando.")
    elif _old_dtype_block in orchestrator_src:
        orchestrator_path.write_text(
            orchestrator_src.replace(_old_dtype_block, _new_dtype_block), encoding="utf-8"
        )
        logger.info("Patch de dtype (float32 em pre-Ampere) aplicado.")
    else:
        raise RuntimeError(
            "O codigo de selecao de dtype pre-Ampere do acestep mudou "
            "upstream -- o patch float16->float32 nao bate mais, atualize "
            "ace_step_server.py (ver acestep/core/generation/handler/"
            "init_service_orchestrator.py)"
        )

    # Confirmed live: requirements.txt's `flash-attn` line has a prebuilt
    # wheel only for win32 -- on Kaggle's Linux kernel it falls through to
    # pip building flash-attn from source, which sat silently (no output)
    # for 20+ minutes with no sign of finishing. Flash Attention is
    # optional and auto-detected at runtime per the acestep package's own
    # GPU_COMPATIBILITY.md ("Flash Attention is auto-detected and enabled
    # when available"), so skip it entirely rather than pay for a slow,
    # fragile from-source build we don't need.
    requirements_path = repo_dir / "requirements.txt"
    all_lines = requirements_path.read_text(encoding="utf-8").splitlines()

    def _is_flash_attn(line: str) -> bool:
        # PEP 503 treats "-" and "_" as equivalent in package names, so
        # match both spellings (flash-attn / flash_attn), case-insensitive.
        normalized = line.strip().lower().replace("_", "-")
        return normalized.startswith("flash-attn")

    kept = [line for line in all_lines if not _is_flash_attn(line)]
    dropped_count = len(all_lines) - len(kept)
    if dropped_count == 0:
        raise RuntimeError(
            "Nenhuma linha 'flash-attn'/'flash_attn' encontrada em "
            f"{requirements_path} -- o requirements.txt do acestep mudou "
            "upstream (dependencia renomeada, movida para outro arquivo, ou "
            "reformatada) e o filtro deste script nao bate mais. Sem esse "
            "filtro, o pip tenta compilar flash-attn do zero, o que trava "
            "silenciosamente por 20+ minutos (o problema que este codigo "
            "existe para evitar) -- atualize ace_step_server.py."
        )
    logger.info(f"Filtrando requirements.txt: {dropped_count} linha(s) de flash-attn removida(s).")

    filtered_requirements_path = repo_dir / "requirements-no-flash-attn.txt"
    filtered_requirements_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    # --no-cache-dir: /kaggle/working ran out of disk on the first live
    # run of this kernel (confirmed live) -- torch's CUDA 12.8 wheel alone
    # is multiple GiB, and pip's default cache keeps a second copy of
    # every downloaded wheel on top of the installed package files.
    logger.info("Instalando dependencias do acestep (sem flash-attn)...")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir",
            "-r", str(filtered_requirements_path),
        ],
        cwd=str(repo_dir),
        check=True,
    )
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir", "-U",
            "fastapi", "uvicorn", "demucs",
        ],
        check=True,
    )
    log_disk_usage("depois do pip install")

    env = os.environ.copy()
    env.update(
        {
            "ACESTEP_API_HOST": "127.0.0.1",
            "ACESTEP_API_PORT": str(_ACESTEP_PORT),
            "ACESTEP_API_KEY": api_key,
            "ACESTEP_CONFIG_PATH": _ACESTEP_MODEL_CONFIG,
            # Not "auto": confirmed live, a real generation (240s, 69%
            # through) failed with "Generation produced NaN or Inf latents"
            # in float16 -- read the acestep source
            # (acestep/core/generation/handler/init_service_loader.py) to
            # find the real cause, since the error message's suggested
            # `ACESTEP_DTYPE=float32` isn't an env var the code actually
            # reads anywhere (only appears in that hint string). The loader
            # already has a guard against exactly this failure mode --
            # pre-Ampere GPUs (T4 = Turing = compute capability 7.5) fall
            # back to "eager" attention (upcasts softmax to float32,
            # avoiding the fp16 SDPA overflow) -- but the guard's condition
            # is `device == "cuda"`, an exact string match. Passing
            # `device="auto"` through (our own default, matching the
            # package's own env-var default) never matches that check, so
            # the guard silently never fires and SDPA's fp16 overflow goes
            # unprotected. Pass "cuda" explicitly so the check matches.
            # Importante: essa mudanca sozinha NAO resolveu o NaN (confirmado
            # ao vivo -- a geracao ainda falhou com o mesmo erro depois dela);
            # o fix de verdade e o patch de dtype acima (float16 -> float32).
            # Mantemos isso mesmo assim porque "auto" tambem bloquearia outras
            # guards de pre-Ampere de dispararem corretamente.
            "ACESTEP_DEVICE": "cuda",
            "ACESTEP_DOWNLOAD_SOURCE": "huggingface",
        }
    )

    output_dir = Path("/kaggle/working/output")

    generation_status = "error"
    generation_error = None
    stems_status = "error"
    stems_error = None
    server_process = None
    demucs_out_dir = Path("/kaggle/working/demucs_out")

    try:
        logger.info(f"Subindo acestep.api_server (config={_ACESTEP_MODEL_CONFIG})...")
        server_process = subprocess.Popen(
            [sys.executable, "-m", "acestep.api_server"],
            cwd=str(repo_dir),
            env=env,
        )
        api_base_url = f"http://127.0.0.1:{_ACESTEP_PORT}"
        output_dir.mkdir(parents=True, exist_ok=True)

        if _JOB_B64 is None:
            raise RuntimeError(
                "_JOB_B64 nao foi definido -- este kernel precisa ser renderizado por "
                "ace_step.kernel_render.render_job_kernel antes de ser enviado ao Kaggle"
            )
        job = decode_job(_JOB_B64)

        logger.info("Esperando acestep.api_server ficar saudavel...")
        wait_for_health(api_base_url, api_key, timeout=600.0, poll_interval=5.0)

        logger.info("Gerando musica...")
        raw_file_ref = wait_for_generation(
            api_base_url, api_key, job, timeout=1200.0, poll_interval=5.0
        )
        source_path = parse_audio_path(raw_file_ref)
        raw_dest = output_dir / "raw.wav"
        shutil.copy(source_path, raw_dest)
        generation_status = "done"
        logger.info(f"Musica gerada e copiada para {raw_dest}.")

        # Encerra o acestep.api_server antes do Demucs: o modelo continua
        # residente na GPU (em float32 em GPUs pre-Ampere -- ver o patch de
        # dtype acima) ate o processo terminar, e Demucs rodando ao lado dele
        # na mesma GPU arrisca CUDA out-of-memory num T4 de 16GB.
        logger.info("Encerrando acestep.api_server antes de rodar Demucs (libera GPU)...")
        server_process.terminate()
        try:
            server_process.wait(timeout=30.0)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait(timeout=30.0)
        server_process = None

        try:
            command = build_demucs_command(raw_dest, demucs_out_dir)
            subprocess.run(command, check=True, capture_output=True, text=True)
            stems = stems_from_output_dir(demucs_out_dir, "htdemucs_6s", raw_dest.stem)
            stems_out_dir = output_dir / "stems"
            stems_out_dir.mkdir(parents=True, exist_ok=True)
            for name, stem_path in stems.items():
                shutil.copy(stem_path, stems_out_dir / f"{name}.wav")
            stems_status = "done"
            logger.info("Separacao de stems concluida.")
        except subprocess.CalledProcessError as exc:
            stems_error = (exc.stderr or "").strip() or str(exc)
            logger.error(f"Separacao de stems falhou: {stems_error}")
        except Exception as exc:
            stems_error = str(exc)
            logger.error(f"Separacao de stems falhou: {stems_error}")
    except Exception as exc:
        generation_error = str(exc)
        logger.error(f"Geracao falhou: {generation_error}")
    finally:
        write_result_json(
            output_dir / "result.json",
            generation_status=generation_status,
            generation_error=generation_error,
            stems_status=stems_status,
            stems_error=stems_error,
        )
        shutil.rmtree(repo_dir, ignore_errors=True)
        shutil.rmtree(demucs_out_dir, ignore_errors=True)
        if server_process is not None:
            server_process.terminate()

    sys.exit(0 if generation_status == "done" else 1)


if __name__ == "__main__":
    main()
