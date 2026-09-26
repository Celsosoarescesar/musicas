from reaper_bridge.mastering import MASTER_CHAIN_PLUGINS, apply_master_chain
from tests.fakes import FakeProject


def test_apply_master_chain_adds_all_plugins_to_master_track():
    project = FakeProject([])
    fxs = apply_master_chain(project)
    assert [fx.name for fx in fxs] == MASTER_CHAIN_PLUGINS
    assert [fx.name for fx in project.master_track.fxs] == MASTER_CHAIN_PLUGINS
