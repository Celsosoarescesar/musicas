import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.mixing import add_fx, set_fx_param, set_mute, set_pan, set_solo, set_volume
from tests.fakes import FakeProject, FakeTrack, FakeFX


def test_set_volume_converts_db_to_linear_gain():
    project = FakeProject([FakeTrack("voz")])
    set_volume(project, "voz", 0.0)
    assert project.tracks[0].volume == pytest.approx(1.0)


def test_set_volume_raises_when_out_of_range():
    project = FakeProject([FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="dB"):
        set_volume(project, "voz", 50.0)


def test_set_pan_sets_value():
    project = FakeProject([FakeTrack("voz")])
    set_pan(project, "voz", -0.5)
    assert project.tracks[0].pan == -0.5


def test_set_pan_raises_when_out_of_range():
    project = FakeProject([FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="pan"):
        set_pan(project, "voz", 2.0)


def test_set_mute_toggles_flag():
    project = FakeProject([FakeTrack("voz")])
    set_mute(project, "voz", True)
    assert project.tracks[0].is_muted is True


def test_set_solo_toggles_flag():
    project = FakeProject([FakeTrack("voz")])
    set_solo(project, "voz", True)
    assert project.tracks[0].is_solo is True


def test_set_volume_wraps_raw_exception():
    """Test that set_volume wraps exceptions when setting track.volume"""
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]

    # Create a property that raises when assigned
    def failing_volume_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    original_volume_attr = FakeTrack.__dict__.get("volume")
    try:
        FakeTrack.volume = property(lambda self: 1.0, failing_volume_setter)
        with pytest.raises(ReaperBridgeError, match="não foi possível definir o volume"):
            set_volume(project, "voz", 0.0)
    finally:
        # Restore original
        if original_volume_attr is None:
            if hasattr(FakeTrack, "volume"):
                delattr(FakeTrack, "volume")
        else:
            FakeTrack.volume = original_volume_attr


def test_set_pan_wraps_raw_exception():
    """Test that set_pan wraps exceptions when setting track.pan"""
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]

    # Create a property that raises when assigned
    def failing_pan_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    original_pan_attr = FakeTrack.__dict__.get("pan")
    try:
        FakeTrack.pan = property(lambda self: 0.0, failing_pan_setter)
        with pytest.raises(ReaperBridgeError, match="não foi possível definir o pan"):
            set_pan(project, "voz", -0.5)
    finally:
        # Restore original
        if original_pan_attr is None:
            if hasattr(FakeTrack, "pan"):
                delattr(FakeTrack, "pan")
        else:
            FakeTrack.pan = original_pan_attr


def test_set_mute_wraps_raw_exception():
    """Test that set_mute wraps exceptions when setting track.is_muted"""
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]

    # Create a property that raises when assigned
    def failing_mute_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    original_mute_attr = FakeTrack.__dict__.get("is_muted")
    try:
        FakeTrack.is_muted = property(lambda self: False, failing_mute_setter)
        with pytest.raises(ReaperBridgeError, match="não foi possível definir o mute"):
            set_mute(project, "voz", True)
    finally:
        # Restore original
        if original_mute_attr is None:
            if hasattr(FakeTrack, "is_muted"):
                delattr(FakeTrack, "is_muted")
        else:
            FakeTrack.is_muted = original_mute_attr


def test_set_solo_wraps_raw_exception():
    """Test that set_solo wraps exceptions when setting track.is_solo"""
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]

    # Create a property that raises when assigned
    def failing_solo_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    original_solo_attr = FakeTrack.__dict__.get("is_solo")
    try:
        FakeTrack.is_solo = property(lambda self: False, failing_solo_setter)
        with pytest.raises(ReaperBridgeError, match="não foi possível definir o solo"):
            set_solo(project, "voz", True)
    finally:
        # Restore original
        if original_solo_attr is None:
            if hasattr(FakeTrack, "is_solo"):
                delattr(FakeTrack, "is_solo")
        else:
            FakeTrack.is_solo = original_solo_attr


def test_add_fx_adds_plugin_to_track():
    project = FakeProject([FakeTrack("voz")])
    fx = add_fx(project, "voz", "ReaEQ (Cockos)")
    assert fx.name == "ReaEQ (Cockos)"
    assert project.tracks[0].fxs[0] is fx


def test_add_fx_raises_when_plugin_unknown():
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]

    def raise_value_error(name):
        raise ValueError("fx not found")

    track.add_fx = raise_value_error
    with pytest.raises(ReaperBridgeError, match="não encontrado"):
        add_fx(project, "voz", "PluginQueNaoExiste")


def test_set_fx_param_updates_normalized_value():
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]
    track.fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold", "Ratio"]))
    set_fx_param(project, "voz", "ReaComp (Cockos)", "Threshold", 0.6)
    assert track.fxs[0].params[0].normalized == 0.6


def test_set_fx_param_raises_for_unknown_param():
    project = FakeProject([FakeTrack("voz")])
    project.tracks[0].fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold"]))
    with pytest.raises(ReaperBridgeError, match="não existe"):
        set_fx_param(project, "voz", "ReaComp (Cockos)", "ParametroInexistente", 0.5)


def test_set_fx_param_raises_when_value_out_of_range():
    project = FakeProject([FakeTrack("voz")])
    project.tracks[0].fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold"]))
    with pytest.raises(ReaperBridgeError, match="0.0 e 1.0"):
        set_fx_param(project, "voz", "ReaComp (Cockos)", "Threshold", 2.0)


def test_set_fx_param_wraps_normalized_setter_exception():
    """Test that set_fx_param wraps exceptions when setting param.normalized.

    This test verifies that the raw reapy call (param.normalized = value) is
    properly wrapped in try/except and converted to ReaperBridgeError.
    """
    project = FakeProject([FakeTrack("voz")])
    track = project.tracks[0]
    track.fxs.append(FakeFX("ReaComp (Cockos)", param_names=["Threshold"]))

    # Replace the param with a fake that raises when normalized is set
    original_param = track.fxs[0].params[0]

    class FailingFakeFXParam:
        def __init__(self, name):
            self.name = name

        @property
        def normalized(self):
            return 0.0

        @normalized.setter
        def normalized(self, value):
            raise RuntimeError("REAPER connection lost")

    track.fxs[0].params[0] = FailingFakeFXParam("Threshold")

    with pytest.raises(ReaperBridgeError, match="não foi possível definir o parâmetro"):
        set_fx_param(project, "voz", "ReaComp (Cockos)", "Threshold", 0.5)

    # Restore for cleanup
    track.fxs[0].params[0] = original_param
