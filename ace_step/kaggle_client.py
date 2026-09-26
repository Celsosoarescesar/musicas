import os

from dotenv import find_dotenv, load_dotenv


class KaggleCredentialsError(Exception):
    """Raised when Kaggle API credentials are missing from the environment."""


class KaggleResourceError(Exception):
    """Raised when a dataset/model/kernel download fails (bad slug, no access, etc.)."""


def ensure_credentials() -> None:
    """Load .env and confirm KAGGLE_USERNAME/KAGGLE_KEY are set.

    Raises:
        KaggleCredentialsError: if either variable is missing.
    """
    load_dotenv(find_dotenv(usecwd=True))
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if not username or not key:
        raise KaggleCredentialsError(
            "KAGGLE_USERNAME e/ou KAGGLE_KEY não encontrados. Copie "
            ".env.example para .env e preencha com o token gerado em "
            "https://www.kaggle.com/settings (seção API)."
        )


def get_kaggle_api():
    """Return an authenticated kaggle.api.kaggle_api_extended.KaggleApi instance."""
    ensure_credentials()
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    return api
