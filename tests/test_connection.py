import time
from unittest.mock import patch

import pytest

from reaper_bridge.connection import get_project
from reaper_bridge.errors import ReaperBridgeError


def test_get_project_returns_project_when_reaper_responds():
    fake_project = object()
    with patch("reaper_bridge.connection.reapy.Project", return_value=fake_project):
        assert get_project(timeout=1.0) is fake_project


def test_get_project_raises_bridge_error_on_timeout():
    def slow_call():
        time.sleep(2)

    with patch("reaper_bridge.connection.reapy.Project", side_effect=slow_call):
        with patch("reaper_bridge.connection.reapy.reconnect") as mock_reconnect:
            start = time.time()
            with pytest.raises(ReaperBridgeError):
                get_project(timeout=0.1)
            elapsed = time.time() - start
    # Ensure we don't hang waiting for the background thread.
    # Two attempts (original + retry after reconnect) at ~0.1s each, not 2s+.
    assert elapsed < 1.0, f"get_project timed out but hung the caller for {elapsed:.2f}s"
    mock_reconnect.assert_called_once()


def test_get_project_raises_bridge_error_on_connection_exception():
    with patch("reaper_bridge.connection.reapy.Project", side_effect=RuntimeError("boom")):
        with patch("reaper_bridge.connection.reapy.reconnect") as mock_reconnect:
            with pytest.raises(ReaperBridgeError):
                get_project(timeout=1.0)
    mock_reconnect.assert_called_once()


def test_get_project_retries_via_reconnect_after_first_failure():
    fake_project = object()
    call_count = {"n": 0}

    def flaky_project(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("not connected yet")
        return fake_project

    with patch("reaper_bridge.connection.reapy.Project", side_effect=flaky_project):
        with patch("reaper_bridge.connection.reapy.reconnect") as mock_reconnect:
            result = get_project(timeout=1.0)

    assert result is fake_project
    mock_reconnect.assert_called_once()
