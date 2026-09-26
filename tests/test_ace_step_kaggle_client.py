import sys
import types

import pytest

from ace_step.kaggle_client import (
    KaggleCredentialsError,
    KaggleResourceError,
    ensure_credentials,
    get_kaggle_api,
)


def test_kaggle_resource_error_is_an_exception():
    assert issubclass(KaggleResourceError, Exception)


def test_ensure_credentials_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(KaggleCredentialsError):
        ensure_credentials()


def test_ensure_credentials_passes_when_set(monkeypatch):
    monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
    monkeypatch.setenv("KAGGLE_KEY", "testkey")
    ensure_credentials()  # must not raise


def test_get_kaggle_api_authenticates(monkeypatch):
    monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
    monkeypatch.setenv("KAGGLE_KEY", "testkey")

    calls = {}

    class FakeApi:
        def authenticate(self):
            calls["authenticated"] = True

    fake_module = types.SimpleNamespace(KaggleApi=FakeApi)
    monkeypatch.setitem(sys.modules, "kaggle.api.kaggle_api_extended", fake_module)

    api = get_kaggle_api()

    assert calls["authenticated"] is True
    assert isinstance(api, FakeApi)
