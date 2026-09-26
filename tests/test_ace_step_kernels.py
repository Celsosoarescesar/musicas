from unittest.mock import MagicMock

import pytest

from ace_step import kernels
from ace_step.kaggle_client import KaggleResourceError


def test_search_kernels_returns_refs(monkeypatch):
    fake_api = MagicMock()
    fake_api.kernels_list.return_value = [
        MagicMock(ref="owner/kernel-a"),
        MagicMock(ref="owner/kernel-b"),
    ]
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    result = kernels.search_kernels("eda")

    fake_api.kernels_list.assert_called_once_with(search="eda")
    assert result == ["owner/kernel-a", "owner/kernel-b"]


def test_download_kernel_creates_dir_and_downloads(monkeypatch, tmp_path):
    fake_api = MagicMock()
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    dest_dir = kernels.download_kernel("owner/kernel-a", dest=tmp_path)

    assert dest_dir == tmp_path / "owner/kernel-a"
    assert dest_dir.exists()
    fake_api.kernels_pull.assert_called_once_with(
        "owner/kernel-a", path=str(dest_dir), metadata=True, quiet=True
    )


def test_download_kernel_wraps_errors_with_slug(monkeypatch, tmp_path):
    fake_api = MagicMock()
    fake_api.kernels_pull.side_effect = RuntimeError("404 Not Found")
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    with pytest.raises(KaggleResourceError, match="owner/does-not-exist"):
        kernels.download_kernel("owner/does-not-exist", dest=tmp_path)


def test_push_kernel_returns_ref(monkeypatch, tmp_path):
    fake_api = MagicMock()
    fake_api.kernels_push.return_value = MagicMock(ref="owner/analise-mercado-br-petr4")
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    ref = kernels.push_kernel(tmp_path)

    fake_api.kernels_push.assert_called_once_with(str(tmp_path))
    assert ref == "owner/analise-mercado-br-petr4"


def test_push_kernel_strips_code_prefix_from_ref(monkeypatch, tmp_path):
    # Real Kaggle behavior: response.ref comes back as a URL path like
    # '/code/owner/slug', not the plain 'owner/slug' that
    # get_kernel_status/pull_kernel_output expect.
    fake_api = MagicMock()
    fake_api.kernels_push.return_value = MagicMock(ref="/code/owner/analise-mercado-br-petr4")
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    ref = kernels.push_kernel(tmp_path)

    assert ref == "owner/analise-mercado-br-petr4"


def test_push_kernel_wraps_errors_with_folder(monkeypatch, tmp_path):
    fake_api = MagicMock()
    fake_api.kernels_push.side_effect = RuntimeError("invalid metadata")
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    with pytest.raises(KaggleResourceError) as exc_info:
        kernels.push_kernel(tmp_path)
    assert str(tmp_path) in str(exc_info.value)


def test_get_kernel_status_returns_status_and_message(monkeypatch):
    from kagglesdk.kernels.types.kernels_enums import KernelWorkerStatus

    fake_api = MagicMock()
    fake_api.kernels_status.return_value = MagicMock(
        status=KernelWorkerStatus.COMPLETE, failure_message=""
    )
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    result = kernels.get_kernel_status("owner/kernel-a")

    fake_api.kernels_status.assert_called_once_with("owner/kernel-a")
    assert result == {"status": "complete", "failure_message": ""}


def test_get_kernel_status_wraps_errors_with_kernel_ref(monkeypatch):
    fake_api = MagicMock()
    fake_api.kernels_status.side_effect = RuntimeError("not found")
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    with pytest.raises(KaggleResourceError, match="owner/does-not-exist"):
        kernels.get_kernel_status("owner/does-not-exist")


def test_pull_kernel_output_creates_dir_and_downloads(monkeypatch, tmp_path):
    fake_api = MagicMock()
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    dest_dir = kernels.pull_kernel_output("owner/kernel-a", tmp_path / "out")

    assert dest_dir == tmp_path / "out"
    assert dest_dir.exists()
    fake_api.kernels_output.assert_called_once_with("owner/kernel-a", path=str(dest_dir))


def test_pull_kernel_output_wraps_errors_with_kernel_ref(monkeypatch, tmp_path):
    fake_api = MagicMock()
    fake_api.kernels_output.side_effect = RuntimeError("not ready")
    monkeypatch.setattr(kernels, "get_kaggle_api", lambda: fake_api)

    with pytest.raises(KaggleResourceError, match="owner/does-not-exist"):
        kernels.pull_kernel_output("owner/does-not-exist", tmp_path / "out")
