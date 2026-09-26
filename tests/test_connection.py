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
        with pytest.raises(ReaperBridgeError):
            get_project(timeout=0.1)


def test_get_project_raises_bridge_error_on_connection_exception():
    with patch("reaper_bridge.connection.reapy.Project", side_effect=RuntimeError("boom")):
        with pytest.raises(ReaperBridgeError):
            get_project(timeout=1.0)
