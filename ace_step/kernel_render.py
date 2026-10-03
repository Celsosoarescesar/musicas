"""Render a self-contained Kaggle kernel folder for one song-generation job.

Kaggle's `script`-type kernel push only uploads a single code file, so
per-run parameters can't be passed as arguments. Instead, the job dict is
JSON-serialized, base64-encoded, and embedded as the `_JOB_B64` module
constant in a copy of `ace_step/kernel/ace_step_server.py`, replacing its
`None` placeholder. See
docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
"""

import base64
import json
import shutil
from pathlib import Path

_KERNEL_DIR = Path(__file__).parent / "kernel"
_TEMPLATE_PATH = _KERNEL_DIR / "ace_step_server.py"
_METADATA_PATH = _KERNEL_DIR / "kernel-metadata.json"
_PLACEHOLDER = "_JOB_B64: str | None = None"


def render_job_kernel(job: dict, dest_dir: Path) -> Path:
    """Render a pushable kernel folder for `job` into `dest_dir`. Returns dest_dir.

    Raises ValueError if the template's `_JOB_B64` placeholder isn't found
    exactly once (the template changed and this function needs updating).
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    source = _TEMPLATE_PATH.read_text(encoding="utf-8")
    occurrences = source.count(_PLACEHOLDER)
    if occurrences != 1:
        raise ValueError(
            f"Esperava exatamente 1 ocorrencia de {_PLACEHOLDER!r} em "
            f"{_TEMPLATE_PATH}, encontrei {occurrences} -- o template mudou, "
            "atualize render_job_kernel."
        )

    job_b64 = base64.b64encode(json.dumps(job, ensure_ascii=False).encode("utf-8")).decode(
        "ascii"
    )
    rendered = source.replace(_PLACEHOLDER, f'_JOB_B64: str | None = "{job_b64}"')
    (dest_dir / "ace_step_server.py").write_text(rendered, encoding="utf-8")

    shutil.copy(_METADATA_PATH, dest_dir / "kernel-metadata.json")
    return dest_dir
