from __future__ import annotations

import concurrent.futures

import reapy

from .errors import ReaperBridgeError

CONNECTION_TIMEOUT_SECONDS = 5.0


def _attempt_get_project(timeout: float) -> "reapy.Project":
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(reapy.Project)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            raise ReaperBridgeError(
                "REAPER não respondeu a tempo. Verifique se o REAPER está aberto e se o "
                "reapy foi configurado corretamente (veja o README)."
            ) from exc
        except Exception as exc:  # reapy pode levantar erros variados de conexão
            raise ReaperBridgeError(
                "REAPER não está aberto ou não foi configurado corretamente, abra o REAPER "
                "e tente de novo."
            ) from exc
    finally:
        executor.shutdown(wait=False)


def get_project(timeout: float = CONNECTION_TIMEOUT_SECONDS) -> "reapy.Project":
    """Retorna o projeto REAPER atualmente aberto, ou levanta ReaperBridgeError.

    Tenta reconectar uma vez (reapy.reconnect()) antes de desistir, cobrindo o
    caso do REAPER ter sido aberto (ou reaberto) depois que este processo já
    existia.
    """
    try:
        return _attempt_get_project(timeout)
    except ReaperBridgeError:
        try:
            reapy.reconnect()
        except Exception:
            pass
        return _attempt_get_project(timeout)
