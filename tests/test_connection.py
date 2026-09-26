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
        start = time.time()
        with pytest.raises(ReaperBridgeError):
            get_project(timeout=0.1)
        elapsed = time.time() - start
        # Ensure we don't hang waiting for the background thread.
        # Should timeout around 0.1s, not wait 2s for the hung call.
        assert elapsed < 1.0, f"get_project timed out but hung the caller for {elapsed:.2f}s"


def test_get_project_raises_bridge_error_on_connection_exception():
    with patch("reaper_bridge.connection.reapy.Project", side_effect=RuntimeError("boom")):
        with pytest.raises(ReaperBridgeError):
            get_project(timeout=1.0)
