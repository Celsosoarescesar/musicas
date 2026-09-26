from pathlib import Path

from ace_step.kaggle_client import KaggleResourceError, get_kaggle_api

NOTEBOOKS_DIR = Path("notebooks")


def search_kernels(query: str) -> list[str]:
    """Return kernel refs (e.g. 'owner/kernel-slug') matching query."""
    api = get_kaggle_api()
    results = api.kernels_list(search=query)
    return [kernel.ref for kernel in results]


def download_kernel(slug: str, dest: Path = NOTEBOOKS_DIR) -> Path:
    """Download a kernel's source code into dest/<slug>/. Returns the destination path."""
    api = get_kaggle_api()
    dest_dir = Path(dest) / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        api.kernels_pull(slug, path=str(dest_dir), metadata=True, quiet=True)
    except Exception as exc:
        raise KaggleResourceError(f"Falha ao baixar kernel '{slug}': {exc}") from exc
    return dest_dir


def push_kernel(folder: Path) -> str:
    """Push a kernel (a folder with kernel-metadata.json + code) to Kaggle.

    Returns the pushed kernel's ref as a plain 'owner/kernel-slug' string,
    usable directly with get_kernel_status/pull_kernel_output.
    """
    api = get_kaggle_api()
    try:
        response = api.kernels_push(str(folder))
    except Exception as exc:
        raise KaggleResourceError(f"Falha ao enviar kernel de '{folder}': {exc}") from exc
    # response.ref comes back as a URL path (e.g. '/code/owner/slug'), not
    # the plain 'owner/slug' that kernels_status/kernels_output expect.
    return response.ref.lstrip("/").removeprefix("code/")


def get_kernel_status(kernel_ref: str) -> dict:
    """Return {'status': str, 'failure_message': str} for a pushed kernel.

    'status' is normalized to a lowercase string (e.g. 'complete',
    'running', 'error') from the Kaggle SDK's KernelWorkerStatus enum.
    """
    api = get_kaggle_api()
    try:
        response = api.kernels_status(kernel_ref)
    except Exception as exc:
        raise KaggleResourceError(
            f"Falha ao consultar status do kernel '{kernel_ref}': {exc}"
        ) from exc
    status = getattr(response.status, "name", response.status)
    return {"status": str(status).lower(), "failure_message": response.failure_message}


def pull_kernel_output(kernel_ref: str, dest: Path) -> Path:
    """Download a finished kernel's output files into dest/. Returns dest."""
    api = get_kaggle_api()
    dest_dir = Path(dest)
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        api.kernels_output(kernel_ref, path=str(dest_dir))
    except Exception as exc:
        raise KaggleResourceError(
            f"Falha ao baixar output do kernel '{kernel_ref}': {exc}"
        ) from exc
    return dest_dir
